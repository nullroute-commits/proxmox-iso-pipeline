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

    # Using community download URL for public accessibility
    PROXMOX_ISO_BASE_URL = "https://download.proxmox.com/iso/proxmox-ve_{version}-1.iso"

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
        if url is None:
            url = self.PROXMOX_ISO_BASE_URL.format(version=self.config.proxmox_version)

        iso_filename = f"proxmox-ve_{self.config.proxmox_version}.iso"
        iso_path = self.config.work_dir / iso_filename

        if iso_path.exists():
            logger.info(f"Using existing ISO: {iso_path}")
            return iso_path

        logger.info(f"Downloading Proxmox ISO from: {url}")

        try:
            # Use wget or curl for downloading
            subprocess.run(
                ["wget", "-O", str(iso_path), url],
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
        all_packages: List[Path] = []

        with Progress() as progress:
            task = progress.add_task("[cyan]Downloading firmware...", total=4)

            # Always download freeware firmware
            packages = self.firmware_manager.download_firmware("freeware")
            all_packages.extend(packages)
            progress.update(task, advance=1)

            # Download vendor-specific firmware if enabled
            if self.config.include_nvidia:
                try:
                    packages = self.firmware_manager.download_firmware("nvidia")
                    all_packages.extend(packages)
                except Exception as e:
                    logger.warning(f"Failed to download NVIDIA firmware: {e}")
            progress.update(task, advance=1)

            if self.config.include_amd:
                try:
                    packages = self.firmware_manager.download_firmware("amd")
                    all_packages.extend(packages)
                except Exception as e:
                    logger.warning(f"Failed to download AMD firmware: {e}")
            progress.update(task, advance=1)

            if self.config.include_intel:
                try:
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
        if self.iso_root is None:
            raise RuntimeError("ISO not extracted yet")

        logger.info("Integrating firmware into ISO...")
        self.firmware_manager.integrate_firmware(firmware_packages, self.iso_root)
        logger.info("Firmware integration complete")

    def rebuild_iso(self, output_name: Optional[str] = None) -> Path:
        """
        Rebuild ISO from modified contents.

        Args:
            output_name: Optional custom output ISO name

        Returns:
            Path to created ISO file

        Raises:
            RuntimeError: If ISO root is not set or rebuild fails
        """
        if self.iso_root is None:
            raise RuntimeError("ISO not extracted yet")

        if output_name is None:
            output_name = f"proxmox-ve_{self.config.proxmox_version}_custom.iso"

        output_path = self.config.output_dir / output_name

        logger.info(f"Rebuilding ISO: {output_path}")

        try:
            # Use xorriso to create bootable ISO
            subprocess.run(
                [
                    "xorriso",
                    "-as",
                    "mkisofs",
                    "-r",
                    "-V",
                    f"Proxmox VE {self.config.proxmox_version}",
                    "-J",
                    "-joliet-long",
                    "-cache-inodes",
                    "-isohybrid-mbr",
                    "/usr/lib/ISOLINUX/isohdpfx.bin",
                    "-b",
                    "isolinux/isolinux.bin",
                    "-c",
                    "isolinux/boot.cat",
                    "-boot-load-size",
                    "4",
                    "-boot-info-table",
                    "-no-emul-boot",
                    "-eltorito-alt-boot",
                    "-e",
                    "efi.img",
                    "-no-emul-boot",
                    "-isohybrid-gpt-basdat",
                    "-o",
                    str(output_path),
                    str(self.iso_root),
                ],
                check=True,
                capture_output=True,
            )

            logger.info(f"ISO created successfully: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to rebuild ISO: {e.stderr}")

    def build(self, iso_url: Optional[str] = None) -> Path:
        """
        Execute complete ISO build process.

        Args:
            iso_url: Optional custom Proxmox ISO URL

        Returns:
            Path to created custom ISO
        """
        console.print("[bold green]Starting Proxmox ISO build process...[/bold green]")

        # Download original ISO
        console.print("[cyan]Step 1/5: Downloading Proxmox ISO[/cyan]")
        iso_path = self.download_iso(iso_url)

        # Extract ISO
        console.print("[cyan]Step 2/5: Extracting ISO[/cyan]")
        self.extract_iso(iso_path)

        # Download firmware
        console.print("[cyan]Step 3/5: Downloading firmware packages[/cyan]")
        firmware_packages = self.download_firmware_packages()

        # Integrate firmware
        console.print("[cyan]Step 4/5: Integrating firmware[/cyan]")
        self.integrate_firmware(firmware_packages)

        # Rebuild ISO
        console.print("[cyan]Step 5/5: Rebuilding ISO[/cyan]")
        output_iso = self.rebuild_iso()

        console.print(f"[bold green]Build complete! ISO: {output_iso}[/bold green]")
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
