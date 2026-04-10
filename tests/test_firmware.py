"""Tests for the FirmwareManager class."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.firmware import (
    FirmwareDownloadError,
    FirmwareIntegrationError,
    FirmwareManager,
    FirmwarePackage,
)


class TestFirmwarePackage:
    """Tests for FirmwarePackage dataclass."""

    def test_basic_creation(self):
        """Test creating a FirmwarePackage with required fields."""
        pkg = FirmwarePackage(
            name="test-firmware",
            vendor="test",
            version="1.0",
            url="http://example.com/fw.deb",
        )
        assert pkg.name == "test-firmware"
        assert pkg.vendor == "test"
        assert pkg.checksum is None
        assert pkg.checksum_type == "sha256"


class TestFirmwareManager:
    """Tests for FirmwareManager."""

    def test_init_creates_cache_dir(self, tmp_path):
        """Test that FirmwareManager creates the cache directory."""
        cache = tmp_path / "new-cache"
        fm = FirmwareManager(cache, "trixie")
        assert cache.exists()
        assert fm.debian_release == "trixie"

    def test_load_firmware_sources_default(self, tmp_path, monkeypatch):
        """Test loading default firmware sources when file doesn't exist."""
        monkeypatch.chdir(tmp_path)
        fm = FirmwareManager(tmp_path / "cache", "trixie")
        assert "freeware" in fm.firmware_sources
        assert "nvidia" in fm.firmware_sources
        assert "amd" in fm.firmware_sources
        assert "intel" in fm.firmware_sources

    def test_load_firmware_sources_from_file(self, tmp_path, monkeypatch):
        """Test loading firmware sources from config file."""
        # Create a config directory with firmware-sources.json
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        sources = {"custom": ["custom-firmware-pkg"]}
        (config_dir / "firmware-sources.json").write_text(json.dumps(sources))

        monkeypatch.chdir(tmp_path)
        fm = FirmwareManager(tmp_path / "cache", "trixie")
        assert "custom" in fm.firmware_sources
        assert fm.firmware_sources["custom"] == ["custom-firmware-pkg"]

    def test_download_firmware_unknown_vendor(self, tmp_path, monkeypatch):
        """Test that unknown vendor raises FirmwareDownloadError."""
        monkeypatch.chdir(tmp_path)
        fm = FirmwareManager(tmp_path / "cache", "trixie")
        with pytest.raises(FirmwareDownloadError, match="Unknown firmware vendor"):
            fm.download_firmware("nonexistent")

    @patch("src.firmware.subprocess.run")
    def test_validate_package_exists(self, mock_run, tmp_path, monkeypatch):
        """Test package validation with apt-cache."""
        monkeypatch.chdir(tmp_path)
        mock_run.return_value = MagicMock(returncode=0)
        fm = FirmwareManager(tmp_path / "cache", "trixie")
        assert fm._validate_package_exists("firmware-linux-free") is True

    @patch("src.firmware.subprocess.run")
    def test_validate_package_not_exists(self, mock_run, tmp_path, monkeypatch):
        """Test package validation when package doesn't exist."""
        monkeypatch.chdir(tmp_path)
        mock_run.return_value = MagicMock(returncode=1)
        fm = FirmwareManager(tmp_path / "cache", "trixie")
        assert fm._validate_package_exists("nonexistent-pkg") is False

    def test_verify_checksum_sha256(self, tmp_path):
        """Test SHA256 checksum verification."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test data for checksum")

        fm = FirmwareManager(tmp_path / "cache", "trixie")

        import hashlib

        expected = hashlib.sha256(b"test data for checksum").hexdigest()
        assert fm.verify_checksum(test_file, expected, "sha256") is True
        assert fm.verify_checksum(test_file, "wrong_hash", "sha256") is False

    def test_verify_checksum_md5(self, tmp_path):
        """Test MD5 checksum verification."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test data")

        fm = FirmwareManager(tmp_path / "cache", "trixie")

        import hashlib

        expected = hashlib.md5(b"test data").hexdigest()
        assert fm.verify_checksum(test_file, expected, "md5") is True

    def test_verify_checksum_unsupported(self, tmp_path):
        """Test unsupported hash type raises ValueError."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test")

        fm = FirmwareManager(tmp_path / "cache", "trixie")
        with pytest.raises(ValueError, match="Unsupported hash type"):
            fm.verify_checksum(test_file, "hash", "sha512")

    @patch("src.firmware.subprocess.run")
    def test_extract_firmware(self, mock_run, tmp_path, monkeypatch):
        """Test firmware extraction from .deb package."""
        monkeypatch.chdir(tmp_path)
        mock_run.return_value = MagicMock(returncode=0)
        fm = FirmwareManager(tmp_path / "cache", "trixie")

        pkg_path = tmp_path / "test.deb"
        pkg_path.write_bytes(b"fake deb")
        dest_dir = tmp_path / "extract"

        fm.extract_firmware(pkg_path, dest_dir)
        assert dest_dir.exists()
        mock_run.assert_called_once()

    @patch("src.firmware.subprocess.run")
    def test_extract_firmware_failure(self, mock_run, tmp_path, monkeypatch):
        """Test firmware extraction failure raises error."""
        monkeypatch.chdir(tmp_path)
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "dpkg-deb")
        fm = FirmwareManager(tmp_path / "cache", "trixie")

        pkg_path = tmp_path / "bad.deb"
        pkg_path.write_bytes(b"bad")

        with pytest.raises(FirmwareIntegrationError):
            fm.extract_firmware(pkg_path, tmp_path / "extract")

    def test_configure_apt_sources_idempotent(self, tmp_path, monkeypatch):
        """Test that _configure_apt_sources is idempotent."""
        monkeypatch.chdir(tmp_path)
        fm = FirmwareManager(tmp_path / "cache", "trixie")
        # Manually set configured flag
        fm._sources_configured = True
        # Should return immediately without running subprocess
        fm._configure_apt_sources()
        assert fm._sources_configured is True
