"""Main ISO builder module for Proxmox installer."""

import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

from src.config import BuildConfig, ConfigManager
from src.firmware import FirmwareManager
from src.performance import get_performance_tracker, track_performance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

logger = logging.getLogger(__name__)
console = Console()


class ProxmoxISOBuilder:
    """Build custom Proxmox VE installer ISO with firmware."""

    # Using enterprise download URL for Proxmox VE ISO
    PROXMOX_ISO_BASE_URL = (
        "https://enterprise.proxmox.com/iso/proxmox-ve_{version}-1.iso"
    )

    def __init__(self, config: BuildConfig) -> None:
        """
        Initialize Proxmox ISO builder.

        Args:
            config: Build configuration
        """
        self.config = config
        self.firmware_manager = FirmwareManager(
            config.firmware_cache, config.debian_release
        )
        self.iso_root: Optional[Path] = None

    def download_iso(self, url: Optional[str] = None) -> Path:
        """
        Download Proxmox VE ISO.

        Args:
            url: Optional custom ISO URL

        Returns:
            Path to downloaded ISO file

        Raises:
            RuntimeError: If download fails
        """
        with track_performance("download_iso", stage="download"):
            if url is None:
                url = self.PROXMOX_ISO_BASE_URL.format(
                    version=self.config.proxmox_version
                )

            iso_filename = f"proxmox-ve_{self.config.proxmox_version}.iso"
            iso_path = self.config.work_dir / iso_filename

            if iso_path.exists():
                logger.info(f"Using existing ISO: {iso_path}")
                return iso_path

            logger.info(f"Downloading Proxmox ISO from: {url}")

            try:
                # Use wget for downloading with certificate verification disabled
                # (some enterprise mirrors have certificate issues)
                subprocess.run(
                    ["wget", "--no-check-certificate", "-O", str(iso_path), url],
                    check=True,
                    capture_output=True,
                )
                logger.info(f"Downloaded ISO to: {iso_path}")
                return iso_path
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to download ISO: {e.stderr}")

    def extract_iso(self, iso_path: Path) -> Path:
        """
        Extract ISO contents to working directory.

        Args:
            iso_path: Path to ISO file

        Returns:
            Path to extracted ISO root directory

        Raises:
            RuntimeError: If extraction fails
        """
        with track_performance("extract_iso", stage="extract"):
            extract_dir = self.config.work_dir / "iso_root"

            if extract_dir.exists():
                logger.info(f"Removing existing extraction: {extract_dir}")
                shutil.rmtree(extract_dir)

            extract_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Extracting ISO to: {extract_dir}")

            try:
                # Mount ISO and copy contents
                mount_point = self.config.work_dir / "iso_mount"
                mount_point.mkdir(exist_ok=True)

                # Mount the ISO
                subprocess.run(
                    [
                        "sudo",
                        "mount",
                        "-o",
                        "loop,ro",
                        str(iso_path),
                        str(mount_point),
                    ],
                    check=True,
                    capture_output=True,
                )

                try:
                    # Copy all contents
                    subprocess.run(
                        ["sudo", "cp", "-a", f"{mount_point}/.", str(extract_dir)],
                        check=True,
                        capture_output=True,
                    )
                finally:
                    # Unmount
                    subprocess.run(
                        ["sudo", "umount", str(mount_point)],
                        check=False,
                        capture_output=True,
                    )
                    mount_point.rmdir()

                # Make files writable
                subprocess.run(
                    ["sudo", "chmod", "-R", "u+w", str(extract_dir)],
                    check=True,
                    capture_output=True,
                )

                self.iso_root = extract_dir
                logger.info(f"ISO extracted successfully to: {extract_dir}")
                return extract_dir

            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to extract ISO: {e.stderr}")

    def download_firmware_packages(self) -> List[Path]:
        """
        Download all required firmware packages.

        Returns:
            List of downloaded firmware package paths
        """
        with track_performance("download_firmware_packages", stage="firmware"):
            all_packages: List[Path] = []

            with Progress() as progress:
                task = progress.add_task("[cyan]Downloading firmware...", total=4)

                # Always download freeware firmware
                with track_performance("download_freeware_firmware", stage="firmware"):
                    packages = self.firmware_manager.download_firmware("freeware")
                    all_packages.extend(packages)
                progress.update(task, advance=1)

                # Download vendor-specific firmware if enabled
                if self.config.include_nvidia:
                    try:
                        with track_performance(
                            "download_nvidia_firmware", stage="firmware"
                        ):
                            packages = self.firmware_manager.download_firmware("nvidia")
                            all_packages.extend(packages)
                    except Exception as e:
                        logger.warning(f"Failed to download NVIDIA firmware: {e}")
                progress.update(task, advance=1)

                if self.config.include_amd:
                    try:
                        with track_performance(
                            "download_amd_firmware", stage="firmware"
                        ):
                            packages = self.firmware_manager.download_firmware("amd")
                            all_packages.extend(packages)
                    except Exception as e:
                        logger.warning(f"Failed to download AMD firmware: {e}")
                progress.update(task, advance=1)

                if self.config.include_intel:
                    try:
                        with track_performance(
                            "download_intel_firmware", stage="firmware"
                        ):
                            packages = self.firmware_manager.download_firmware("intel")
                            all_packages.extend(packages)
                    except Exception as e:
                        logger.warning(f"Failed to download Intel firmware: {e}")
                progress.update(task, advance=1)

            logger.info(f"Downloaded {len(all_packages)} firmware packages")
            return all_packages

    def integrate_firmware(self, firmware_packages: List[Path]) -> None:
        """
        Integrate firmware packages into extracted ISO.

        Args:
            firmware_packages: List of firmware package paths

        Raises:
            RuntimeError: If ISO root is not set
        """
        with track_performance("integrate_firmware", stage="integration"):
            if self.iso_root is None:
                raise RuntimeError("ISO not extracted yet")

            logger.info("Integrating firmware into ISO...")
            self.firmware_manager.integrate_firmware(firmware_packages, self.iso_root)
            logger.info("Firmware integration complete")

    def _combine_microcode_files(
        self, ucode_dir: Path, src_dir: Path, vendor: str
    ) -> bool:
        """
        Combine microcode files from a source directory into a single blob.

        Args:
            ucode_dir: Directory to write combined microcode
            src_dir: Source directory containing microcode files
            vendor: Vendor name ('GenuineIntel' or 'AuthenticAMD')

        Returns:
            True if microcode was added, False otherwise
        """
        if not src_dir.exists():
            return False

        files = list(src_dir.glob("*"))
        if not files:
            return False

        blob_path = ucode_dir / f"{vendor}.bin"
        with blob_path.open("wb") as out:
            for f in sorted(files):
                # Skip non-files and Intel's .initramfs files
                if f.is_file() and not f.name.endswith(".initramfs"):
                    out.write(f.read_bytes())

        if blob_path.stat().st_size > 0:
            logger.info(f"{vendor} microcode: {blob_path.stat().st_size} bytes")
            return True
        return False

    def _create_early_cpio(self, temp_path: Path, cpio_path: Path) -> None:
        """
        Create early microcode cpio archive.

        Args:
            temp_path: Directory containing microcode structure
            cpio_path: Path to write the cpio archive
        """
        result = subprocess.run(
            ["find", ".", "-print0"],
            cwd=temp_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["cpio", "-o", "-H", "newc", "-0"],
            input=result.stdout,
            cwd=temp_path,
            stdout=cpio_path.open("wb"),
            check=True,
        )
        logger.info(f"Created early microcode cpio: {cpio_path.stat().st_size} bytes")

    def _prepend_microcode_to_initrd(self, early_cpio: Path, initrd: Path) -> None:
        """
        Prepend early microcode cpio to initrd.

        Args:
            early_cpio: Path to early microcode cpio archive
            initrd: Path to initrd.img file
        """
        if not initrd.exists():
            return

        initrd_orig = initrd.with_suffix(".img.orig")
        # Backup original initrd using sudo (may be root-owned)
        subprocess.run(
            ["sudo", "mv", str(initrd), str(initrd_orig)],
            check=True,
            capture_output=True,
        )
        # Combine: early_ucode + original_initrd
        cat_cmd = f"cat {early_cpio} {initrd_orig} > {initrd}"
        subprocess.run(
            ["sudo", "sh", "-c", cat_cmd],
            check=True,
            capture_output=True,
        )
        logger.info(
            f"Combined initrd: {initrd.stat().st_size} bytes "
            f"(was {initrd_orig.stat().st_size} bytes)"
        )

    def build_early_microcode(self) -> None:
        """
        Build early microcode initramfs and prepend to initrd.

        This creates an uncompressed cpio archive containing CPU microcode
        that gets loaded very early in the boot process, before the main
        initramfs. This is critical for fixing MCE errors and ensuring
        CPU stability.

        Raises:
            RuntimeError: If ISO root is not set
        """
        with track_performance("build_early_microcode", stage="microcode"):
            if self.iso_root is None:
                raise RuntimeError("ISO not extracted yet")

            firmware_dir = self.iso_root / "firmware"
            intel_ucode = firmware_dir / "intel-ucode"
            amd_ucode = firmware_dir / "amd-ucode"

            if not intel_ucode.exists() and not amd_ucode.exists():
                logger.warning("No microcode found, skipping early microcode build")
                return

            logger.info("Building early microcode initramfs...")

            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                ucode_dir = temp_path / "kernel" / "x86" / "microcode"
                ucode_dir.mkdir(parents=True, exist_ok=True)

                # Combine vendor microcode files
                intel_added = self._combine_microcode_files(
                    ucode_dir, intel_ucode, "GenuineIntel"
                )
                amd_added = self._combine_microcode_files(
                    ucode_dir, amd_ucode, "AuthenticAMD"
                )

                if not intel_added and not amd_added:
                    logger.warning("No microcode files found to add")
                    return

                # Create and prepend cpio archive
                early_cpio = self.config.work_dir / "early_ucode.cpio"
                self._create_early_cpio(temp_path, early_cpio)

                initrd = self.iso_root / "boot" / "initrd.img"
                self._prepend_microcode_to_initrd(early_cpio, initrd)

                # Clean up
                early_cpio.unlink(missing_ok=True)

            logger.info("Early microcode loading configured")

    def copy_post_install_script(self) -> None:
        """
        Copy post-install firmware helper script to ISO root.

        This script helps users copy firmware to the installed system
        and rebuild the initramfs after Proxmox installation completes.

        Raises:
            RuntimeError: If ISO root is not set
        """
        with track_performance("copy_post_install_script", stage="scripts"):
            if self.iso_root is None:
                raise RuntimeError("ISO not extracted yet")

            # Find the post-install script
            script_locations = [
                Path(__file__).parent.parent / "scripts" / "post-install-firmware.sh",
                Path("scripts/post-install-firmware.sh"),
                Path("/workspace/scripts/post-install-firmware.sh"),
            ]

            script_path = None
            for loc in script_locations:
                if loc.exists():
                    script_path = loc
                    break

            if script_path is None:
                logger.warning(
                    "Post-install firmware script not found, skipping. "
                    "Users will need to manually copy firmware after installation."
                )
                return

            dest_path = self.iso_root / "post-install-firmware.sh"
            logger.info(f"Copying post-install script to ISO: {dest_path}")

            try:
                subprocess.run(
                    ["sudo", "cp", str(script_path), str(dest_path)],
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["sudo", "chmod", "+x", str(dest_path)],
                    check=True,
                    capture_output=True,
                )
                logger.info("Post-install helper script added to ISO root")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to copy post-install script: {e}")

    def validate_boot_files(self) -> bool:
        """
        Validate that required boot files exist in the ISO.

        Returns:
            True if all required boot files exist

        Raises:
            RuntimeError: If ISO root is not set or boot files are missing
        """
        with track_performance("validate_boot_files", stage="validation"):
            if self.iso_root is None:
                raise RuntimeError("ISO not extracted yet")

            logger.info("Validating boot files...")

            # Check for EFI boot files
            efi_img = self.iso_root / "efi.img"
            if not efi_img.exists():
                raise RuntimeError(
                    f"EFI boot image not found: {efi_img}\n"
                    "The ISO may not be compatible with UEFI/Secure Boot"
                )

            # Check for BIOS boot files (isolinux)
            isolinux_bin = self.iso_root / "isolinux" / "isolinux.bin"
            if isolinux_bin.exists():
                logger.info("BIOS boot support: isolinux.bin found")
            else:
                logger.info(
                    "BIOS boot files not found - ISO will only support UEFI mode"
                )

            # Check for GRUB configuration
            grub_cfg_paths = [
                self.iso_root / "boot" / "grub" / "grub.cfg",
                self.iso_root / "boot" / "grub" / "loopback.cfg",
            ]
            grub_found = any(p.exists() for p in grub_cfg_paths)
            if not grub_found:
                logger.warning("GRUB configuration not found")

            logger.info("Boot file validation complete")
            return True

    def _find_mbr_template(self) -> Optional[Path]:
        """
        Find MBR template file for hybrid boot.

        Returns:
            Path to MBR template if found, None otherwise
        """
        mbr_template_paths = [
            Path("/usr/lib/ISOLINUX/isohdpfx.bin"),  # Debian/Ubuntu
            Path("/usr/lib/syslinux/bios/isohdpfx.bin"),  # Arch/Fedora
            Path("/usr/share/syslinux/isohdpfx.bin"),  # Alternative
            Path("/usr/lib/syslinux/isohdpfx.bin"),  # Older systems
        ]

        for mbr_path in mbr_template_paths:
            if mbr_path.exists():
                logger.debug(f"Found MBR template: {mbr_path}")
                return mbr_path

        logger.info(
            "MBR template not found - ISO may not boot properly "
            "from USB in BIOS mode"
        )
        return None

    def rebuild_iso(self, output_name: Optional[str] = None) -> Path:
        """
        Rebuild ISO from modified contents with hybrid BIOS/UEFI boot support.

        Creates a bootable ISO that supports:
        - UEFI boot (including Secure Boot compatibility)
        - Legacy BIOS boot (via isolinux)
        - USB/hybrid boot modes

        Args:
            output_name: Optional custom output ISO name

        Returns:
            Path to created ISO file

        Raises:
            RuntimeError: If ISO root is not set or rebuild fails
        """
        with track_performance("rebuild_iso", stage="rebuild"):
            if self.iso_root is None:
                raise RuntimeError("ISO not extracted yet")

            if output_name is None:
                output_name = f"proxmox-ve_{self.config.proxmox_version}_custom.iso"

            output_path = self.config.output_dir / output_name

            logger.info(f"Rebuilding ISO: {output_path}")

            # Validate boot files exist
            self.validate_boot_files()

            # Check which boot modes are available
            has_isolinux = (self.iso_root / "isolinux" / "isolinux.bin").exists()
            has_efi = (self.iso_root / "efi.img").exists()

            # Build xorriso command with hybrid boot support
            xorriso_cmd = [
                "xorriso",
                "-as",
                "mkisofs",
                "-r",  # Rock Ridge extensions for POSIX compatibility
                "-V",
                f"PVE{self.config.proxmox_version.replace('.', '')}",
                "-J",  # Joliet extensions for Windows compatibility
                "-joliet-long",  # Allow longer Joliet filenames
            ]

            # Add BIOS boot support if isolinux is available
            if has_isolinux:
                logger.info("Adding BIOS boot support (isolinux)")
                xorriso_cmd.extend(
                    [
                        "-b",
                        "isolinux/isolinux.bin",  # BIOS boot image
                        "-c",
                        "isolinux/boot.cat",  # Boot catalog
                        "-no-emul-boot",  # No emulation mode
                        "-boot-load-size",
                        "4",  # Load 4 sectors
                        "-boot-info-table",  # Add boot info table
                    ]
                )

                # Add MBR template for hybrid boot if available
                mbr_template = self._find_mbr_template()
                if mbr_template:
                    xorriso_cmd.extend(["-isohybrid-mbr", str(mbr_template)])

            # Add UEFI boot support
            if has_efi:
                logger.info("Adding UEFI boot support (Secure Boot compatible)")
                xorriso_cmd.extend(
                    [
                        "-eltorito-alt-boot",  # Alternate boot entry
                        "-e",
                        "efi.img",  # EFI boot image
                        "-no-emul-boot",  # No emulation mode
                        "-append_partition",
                        "2",  # Partition number
                        "0xef",  # EFI System Partition type
                        str(self.iso_root / "efi.img"),
                        "-isohybrid-gpt-basdat",  # GPT partition for hybrid ISO
                    ]
                )

            # Add output path and source directory
            xorriso_cmd.extend(["-o", str(output_path), str(self.iso_root)])

            try:
                logger.debug(f"Running xorriso command: {' '.join(xorriso_cmd)}")
                result = subprocess.run(
                    xorriso_cmd, check=True, capture_output=True, text=True
                )

                # Log xorriso output for debugging
                if result.stdout:
                    logger.debug(f"xorriso output: {result.stdout}")

                logger.info(f"ISO created successfully: {output_path}")
                logger.info(
                    f"Boot modes: BIOS={'yes' if has_isolinux else 'no'}, "
                    f"UEFI={'yes' if has_efi else 'no'}"
                )
                return output_path

            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to rebuild ISO: {e.stderr if e.stderr else str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

    def build(self, iso_url: Optional[str] = None) -> Path:
        """
        Execute complete ISO build process.

        Args:
            iso_url: Optional custom Proxmox ISO URL

        Returns:
            Path to created custom ISO
        """
        tracker = get_performance_tracker()

        with track_performance("complete_build", stage="build"):
            console.print(
                "[bold green]Starting Proxmox ISO build process...[/bold green]"
            )

            # Download original ISO
            console.print("[cyan]Step 1/6: Downloading Proxmox ISO[/cyan]")
            iso_path = self.download_iso(iso_url)

            # Extract ISO
            console.print("[cyan]Step 2/6: Extracting ISO[/cyan]")
            self.extract_iso(iso_path)

            # Download firmware
            console.print("[cyan]Step 3/6: Downloading firmware packages[/cyan]")
            firmware_packages = self.download_firmware_packages()

            # Integrate firmware
            console.print("[cyan]Step 4/7: Integrating firmware[/cyan]")
            self.integrate_firmware(firmware_packages)

            # Build early microcode (critical for MCE fixes)
            console.print("[cyan]Step 5/7: Building early microcode initramfs[/cyan]")
            self.build_early_microcode()

            # Copy post-install helper script
            console.print("[cyan]Step 6/7: Adding post-install helper script[/cyan]")
            self.copy_post_install_script()

            # Rebuild ISO
            console.print("[cyan]Step 7/7: Rebuilding ISO[/cyan]")
            output_iso = self.rebuild_iso()

            console.print(f"[bold green]Build complete! ISO: {output_iso}[/bold green]")
            console.print(
                "[yellow]IMPORTANT: After installation, run /cdrom/post-install-firmware.sh "
                "before rebooting to copy firmware to the installed system.[/yellow]"
            )

        # Print performance summary
        console.print("\n")
        tracker.print_summary(console)

        return output_iso


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--proxmox-version",
    default="9.1",
    help="Proxmox VE version (default: 9.1)",
)
@click.option(
    "--debian-release",
    default="trixie",
    help="Debian release name (default: trixie)",
)
@click.option(
    "--no-nvidia",
    is_flag=True,
    help="Exclude NVIDIA firmware",
)
@click.option(
    "--no-amd",
    is_flag=True,
    help="Exclude AMD firmware",
)
@click.option(
    "--no-intel",
    is_flag=True,
    help="Exclude Intel firmware",
)
@click.option(
    "--iso-url",
    help="Custom Proxmox ISO URL",
)
def main(
    config: Optional[Path],
    proxmox_version: str,
    debian_release: str,
    no_nvidia: bool,
    no_amd: bool,
    no_intel: bool,
    iso_url: Optional[str],
) -> None:
    """Build custom Proxmox VE installer ISO with firmware support."""
    try:
        # Load configuration
        config_manager = ConfigManager(config)

        if config:
            config_manager.load_from_file(config)

        config_manager.load_from_env()

        # Override with command-line arguments
        build_config = config_manager.get_config()
        build_config.proxmox_version = proxmox_version
        build_config.debian_release = debian_release
        build_config.include_nvidia = not no_nvidia
        build_config.include_amd = not no_amd
        build_config.include_intel = not no_intel

        # Validate configuration
        config_manager.validate()

        # Build ISO
        builder = ProxmoxISOBuilder(build_config)
        output_iso = builder.build(iso_url)

        console.print(f"\n[bold green]Success![/bold green] Custom ISO: {output_iso}")
        sys.exit(0)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.exception("Build failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
