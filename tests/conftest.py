"""Shared fixtures for Proxmox ISO Pipeline tests."""

import json

import pytest


@pytest.fixture
def tmp_work_dir(tmp_path):
    """Create a temporary work directory structure."""
    output_dir = tmp_path / "output"
    work_dir = tmp_path / "work"
    cache_dir = tmp_path / "firmware-cache"
    output_dir.mkdir()
    work_dir.mkdir()
    cache_dir.mkdir()
    return tmp_path


@pytest.fixture
def firmware_sources_file(tmp_path):
    """Create a temporary firmware-sources.json for testing."""
    sources = {
        "freeware": [
            "firmware-linux-free",
            "firmware-misc-nonfree",
        ],
        "nvidia": [
            "firmware-nvidia-graphics",
        ],
        "amd": [
            "firmware-amd-graphics",
            "amd64-microcode",
        ],
        "intel": [
            "intel-microcode",
        ],
    }
    sources_file = tmp_path / "firmware-sources.json"
    sources_file.write_text(json.dumps(sources))
    return sources_file


@pytest.fixture
def mock_iso_root(tmp_path):
    """Create a mock ISO root structure for testing."""
    iso_root = tmp_path / "iso_root"
    iso_root.mkdir()

    # Create minimal boot structure
    boot_dir = iso_root / "boot"
    boot_dir.mkdir()
    grub_dir = boot_dir / "grub"
    grub_dir.mkdir()
    (grub_dir / "grub.cfg").write_text("# GRUB config")

    # Create a fake initrd
    (boot_dir / "initrd.img").write_bytes(b"\x00" * 1024)

    # Create EFI image
    (iso_root / "efi.img").write_bytes(b"\x00" * 512)

    # Create isolinux directory
    isolinux_dir = iso_root / "isolinux"
    isolinux_dir.mkdir()
    (isolinux_dir / "isolinux.bin").write_bytes(b"\x00" * 256)

    return iso_root
