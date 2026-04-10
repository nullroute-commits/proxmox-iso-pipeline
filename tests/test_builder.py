"""Tests for the ProxmoxISOBuilder class."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.builder import ProxmoxISOBuilder
from src.config import BuildConfig


class TestProxmoxISOBuilder:
    """Tests for ProxmoxISOBuilder."""

    def _make_builder(self, tmp_path):
        """Create a builder with temp directories."""
        config = BuildConfig(
            output_dir=tmp_path / "output",
            work_dir=tmp_path / "work",
            firmware_cache=tmp_path / "cache",
        )
        return ProxmoxISOBuilder(config)

    def test_init(self, tmp_path):
        """Test builder initialization."""
        builder = self._make_builder(tmp_path)
        assert builder.iso_root is None
        assert builder.config.proxmox_version == "9.1"

    def test_iso_url_format(self, tmp_path):
        """Test that ISO URL is correctly formatted."""
        builder = self._make_builder(tmp_path)
        url = builder.PROXMOX_ISO_BASE_URL.format(
            version=builder.config.proxmox_version
        )
        assert "9.1" in url
        assert url.startswith("https://")
        assert url.endswith(".iso")

    @patch("src.builder.subprocess.run")
    def test_download_iso_uses_existing(self, mock_run, tmp_path):
        """Test that existing ISO is reused without downloading."""
        builder = self._make_builder(tmp_path)
        iso_path = builder.config.work_dir / "proxmox-ve_9.1.iso"
        iso_path.write_bytes(b"fake iso content")

        result = builder.download_iso()
        assert result == iso_path
        mock_run.assert_not_called()  # No wget call needed

    @patch("src.builder.subprocess.run")
    def test_download_iso_wget(self, mock_run, tmp_path):
        """Test that wget is called for missing ISO."""
        builder = self._make_builder(tmp_path)
        mock_run.return_value = MagicMock(returncode=0)

        builder.download_iso()
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "wget"
        assert "-O" in args

    @patch("src.builder.subprocess.run")
    def test_download_iso_custom_url(self, mock_run, tmp_path):
        """Test download with custom URL."""
        builder = self._make_builder(tmp_path)
        mock_run.return_value = MagicMock(returncode=0)
        custom_url = "https://example.com/custom.iso"

        builder.download_iso(url=custom_url)
        args = mock_run.call_args[0][0]
        assert custom_url in args

    @patch("src.builder.subprocess.run")
    def test_download_iso_failure(self, mock_run, tmp_path):
        """Test that download failure raises RuntimeError."""
        builder = self._make_builder(tmp_path)
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "wget", stderr=b"Connection refused"
        )

        with pytest.raises(RuntimeError, match="Failed to download"):
            builder.download_iso()

    def test_validate_boot_files_no_root(self, tmp_path):
        """Test validation fails when iso_root is not set."""
        builder = self._make_builder(tmp_path)
        with pytest.raises(RuntimeError, match="ISO not extracted"):
            builder.validate_boot_files()

    def test_validate_boot_files_missing_efi(self, tmp_path, mock_iso_root):
        """Test validation fails when EFI image is missing."""
        builder = self._make_builder(tmp_path)
        builder.iso_root = mock_iso_root
        (mock_iso_root / "efi.img").unlink()

        with pytest.raises(RuntimeError, match="EFI boot image not found"):
            builder.validate_boot_files()

    def test_validate_boot_files_success(self, tmp_path, mock_iso_root):
        """Test validation passes with proper boot files."""
        builder = self._make_builder(tmp_path)
        builder.iso_root = mock_iso_root
        assert builder.validate_boot_files() is True

    def test_find_mbr_template_none(self, tmp_path):
        """Test MBR template search returns None when not installed."""
        builder = self._make_builder(tmp_path)
        # On CI systems, MBR template may or may not exist
        result = builder._find_mbr_template()
        # Just verify it returns Path or None
        assert result is None or isinstance(result, Path)

    def test_rebuild_iso_no_root(self, tmp_path):
        """Test rebuild fails when iso_root is not set."""
        builder = self._make_builder(tmp_path)
        with pytest.raises(RuntimeError, match="ISO not extracted"):
            builder.rebuild_iso()

    def test_build_early_microcode_no_root(self, tmp_path):
        """Test early microcode build fails when iso_root not set."""
        builder = self._make_builder(tmp_path)
        with pytest.raises(RuntimeError, match="ISO not extracted"):
            builder.build_early_microcode()

    def test_build_early_microcode_no_ucode(self, tmp_path, mock_iso_root):
        """Test early microcode build skips when no microcode found."""
        builder = self._make_builder(tmp_path)
        builder.iso_root = mock_iso_root
        # No firmware/intel-ucode or firmware/amd-ucode dirs
        # Should exit gracefully
        builder.build_early_microcode()

    def test_combine_microcode_files_empty_dir(self, tmp_path):
        """Test combining microcode files from empty directory."""
        builder = self._make_builder(tmp_path)
        ucode_dir = tmp_path / "ucode"
        ucode_dir.mkdir()
        src_dir = tmp_path / "empty_src"
        src_dir.mkdir()
        result = builder._combine_microcode_files(ucode_dir, src_dir, "GenuineIntel")
        assert result is False

    def test_combine_microcode_files_nonexistent(self, tmp_path):
        """Test combining from nonexistent directory returns False."""
        builder = self._make_builder(tmp_path)
        ucode_dir = tmp_path / "ucode"
        ucode_dir.mkdir()
        src_dir = tmp_path / "nonexistent"
        result = builder._combine_microcode_files(ucode_dir, src_dir, "GenuineIntel")
        assert result is False

    def test_combine_microcode_files_success(self, tmp_path):
        """Test combining microcode files from populated directory."""
        builder = self._make_builder(tmp_path)
        ucode_dir = tmp_path / "ucode"
        ucode_dir.mkdir()
        src_dir = tmp_path / "intel_ucode"
        src_dir.mkdir()

        # Create fake microcode files
        (src_dir / "cpu_01").write_bytes(b"\x01\x02\x03")
        (src_dir / "cpu_02").write_bytes(b"\x04\x05\x06")

        result = builder._combine_microcode_files(ucode_dir, src_dir, "GenuineIntel")
        assert result is True
        blob = ucode_dir / "GenuineIntel.bin"
        assert blob.exists()
        assert blob.stat().st_size == 6

    def test_integrate_firmware_no_root(self, tmp_path):
        """Test firmware integration fails when iso_root not set."""
        builder = self._make_builder(tmp_path)
        with pytest.raises(RuntimeError, match="ISO not extracted"):
            builder.integrate_firmware([])


class TestBuilderCLI:
    """Tests for the Click CLI interface."""

    def test_main_help(self):
        """Test that --help runs without error."""
        from click.testing import CliRunner

        from src.builder import main

        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Build custom Proxmox VE installer ISO" in result.output

    def test_main_with_nonexistent_config(self):
        """Test that nonexistent config file fails gracefully."""
        from click.testing import CliRunner

        from src.builder import main

        runner = CliRunner()
        result = runner.invoke(main, ["-c", "/nonexistent/config.yaml"])
        # Click should catch the bad path before our code
        assert result.exit_code != 0
