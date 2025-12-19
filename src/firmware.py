"""Firmware integration module for Proxmox ISO builder."""

import hashlib
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


@dataclass
class FirmwarePackage:
    """Firmware package information."""

    name: str
    vendor: str
    version: str
    url: str
    checksum: Optional[str] = None
    checksum_type: str = "sha256"


class FirmwareError(Exception):
    """Base exception for firmware operations."""

    pass


class FirmwareDownloadError(FirmwareError):
    """Exception raised when firmware download fails."""

    pass


class FirmwareIntegrationError(FirmwareError):
    """Exception raised when firmware integration fails."""

    pass


class FirmwareManager:
    """Manage firmware download and integration."""

    DEBIAN_REPO_BASE = "http://deb.debian.org/debian"
    FIRMWARE_SOURCES_FILE = "config/firmware-sources.json"

    def __init__(
        self, cache_dir: Path, debian_release: str = "trixie"
    ) -> None:
        """
        Initialize firmware manager.

        Args:
            cache_dir: Directory for caching firmware packages
            debian_release: Debian release name (default: trixie)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.debian_release = debian_release
        self.firmware_sources = self._load_firmware_sources()

    def _load_firmware_sources(self) -> Dict[str, List[str]]:
        """
        Load firmware sources from configuration file.

        Returns:
            Dictionary mapping vendor to list of package names
        """
        sources_file = Path(self.FIRMWARE_SOURCES_FILE)
        if sources_file.exists():
            with sources_file.open() as f:
                return json.load(f)

        # Default firmware sources
        return {
            "freeware": [
                "firmware-linux-free",
                "firmware-misc-nonfree",
            ],
            "nvidia": [
                "nvidia-driver",
                "nvidia-firmware-graphics",
                "firmware-nvidia-graphics",
            ],
            "amd": [
                "amdgpu-firmware",
                "firmware-amd-graphics",
                "amd64-microcode",
            ],
            "intel": [
                "intel-microcode",
                "firmware-intel-sound",
                "i915-firmware",
            ],
        }

    def download_firmware(
        self, vendor: str, force: bool = False
    ) -> List[Path]:
        """
        Download firmware packages for specified vendor.

        Args:
            vendor: Hardware vendor name (nvidia, amd, intel, freeware)
            force: Force re-download even if cached

        Returns:
            List of paths to downloaded firmware packages

        Raises:
            FirmwareDownloadError: If download fails
        """
        if vendor not in self.firmware_sources:
            raise FirmwareDownloadError(f"Unknown firmware vendor: {vendor}")

        packages = self.firmware_sources[vendor]
        downloaded_files: List[Path] = []

        logger.info(f"Downloading {vendor} firmware packages: {packages}")

        for package_name in packages:
            try:
                file_path = self._download_package(package_name, force)
                if file_path:
                    downloaded_files.append(file_path)
                    logger.info(f"Downloaded: {file_path}")
            except Exception as e:
                logger.warning(
                    f"Failed to download {package_name}: {e}"
                )
                # Continue with other packages

        if not downloaded_files:
            raise FirmwareDownloadError(
                f"No firmware packages downloaded for {vendor}"
            )

        return downloaded_files

    def _download_package(
        self, package_name: str, force: bool = False
    ) -> Optional[Path]:
        """
        Download a single Debian package.

        Args:
            package_name: Name of the Debian package
            force: Force re-download even if cached

        Returns:
            Path to downloaded package or None if already cached
        """
        cache_file = self.cache_dir / f"{package_name}.deb"

        if cache_file.exists() and not force:
            logger.debug(f"Using cached package: {cache_file}")
            return cache_file

        # Use apt-get download in a container or direct URL
        # For simplicity, we'll use subprocess with apt-get
        try:
            subprocess.run(
                [
                    "apt-get",
                    "download",
                    "-t",
                    self.debian_release,
                    package_name,
                ],
                cwd=self.cache_dir,
                check=True,
                capture_output=True,
            )

            # Find the downloaded .deb file
            deb_files = list(self.cache_dir.glob(f"{package_name}*.deb"))
            if deb_files:
                return deb_files[0]

        except subprocess.CalledProcessError as e:
            logger.error(
                f"apt-get download failed for {package_name}: {e.stderr}"
            )

        return None

    def extract_firmware(
        self, package_path: Path, dest_dir: Path
    ) -> None:
        """
        Extract firmware files from Debian package.

        Args:
            package_path: Path to .deb package
            dest_dir: Destination directory for extracted files

        Raises:
            FirmwareIntegrationError: If extraction fails
        """
        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Extract .deb package using dpkg-deb
            subprocess.run(
                ["dpkg-deb", "-x", str(package_path), str(dest_dir)],
                check=True,
                capture_output=True,
            )
            logger.info(f"Extracted {package_path} to {dest_dir}")
        except subprocess.CalledProcessError as e:
            raise FirmwareIntegrationError(
                f"Failed to extract {package_path}: {e.stderr}"
            )

    def verify_checksum(
        self, file_path: Path, expected_hash: str, hash_type: str = "sha256"
    ) -> bool:
        """
        Verify file checksum.

        Args:
            file_path: Path to file to verify
            expected_hash: Expected hash value
            hash_type: Hash algorithm (default: sha256)

        Returns:
            True if checksum matches, False otherwise
        """
        if hash_type == "sha256":
            hasher = hashlib.sha256()
        elif hash_type == "md5":
            hasher = hashlib.md5()
        else:
            raise ValueError(f"Unsupported hash type: {hash_type}")

        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)

        actual_hash = hasher.hexdigest()
        return actual_hash == expected_hash

    def integrate_firmware(
        self, firmware_files: List[Path], iso_root: Path
    ) -> None:
        """
        Integrate firmware files into ISO root.

        Args:
            firmware_files: List of firmware package paths
            iso_root: Root directory of extracted ISO

        Raises:
            FirmwareIntegrationError: If integration fails
        """
        firmware_dir = iso_root / "firmware"
        firmware_dir.mkdir(parents=True, exist_ok=True)

        for package_path in firmware_files:
            try:
                # Extract to temporary directory
                temp_extract = self.cache_dir / "temp_extract"
                temp_extract.mkdir(exist_ok=True)

                self.extract_firmware(package_path, temp_extract)

                # Copy firmware files to ISO
                lib_firmware = temp_extract / "lib" / "firmware"
                if lib_firmware.exists():
                    for item in lib_firmware.rglob("*"):
                        if item.is_file():
                            rel_path = item.relative_to(lib_firmware)
                            dest = firmware_dir / rel_path
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, dest)
                            logger.debug(f"Copied firmware: {rel_path}")

                # Clean up
                shutil.rmtree(temp_extract, ignore_errors=True)

            except Exception as e:
                logger.error(f"Failed to integrate {package_path}: {e}")
                raise FirmwareIntegrationError(
                    f"Firmware integration failed: {e}"
                )

        logger.info(
            f"Successfully integrated {len(firmware_files)} firmware packages"
        )
