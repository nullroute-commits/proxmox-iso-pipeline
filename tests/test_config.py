"""Tests for the BuildConfig and ConfigManager classes."""

import json

import pytest
import yaml

from src.config import BuildConfig, ConfigManager


class TestBuildConfig:
    """Tests for BuildConfig dataclass."""

    def test_default_values(self, tmp_path, monkeypatch):
        """Test that BuildConfig has sensible defaults."""
        monkeypatch.chdir(tmp_path)
        config = BuildConfig()
        assert config.proxmox_version == "9.1"
        assert config.debian_release == "trixie"
        assert config.include_nvidia is True
        assert config.include_amd is True
        assert config.include_intel is True
        assert config.build_arch == ["linux/amd64", "linux/arm64", "linux/loong64"]

    def test_custom_values(self, tmp_path):
        """Test BuildConfig with custom values."""
        config = BuildConfig(
            proxmox_version="8.2",
            debian_release="bookworm",
            include_nvidia=False,
            include_amd=False,
            include_intel=True,
            output_dir=tmp_path / "out",
            work_dir=tmp_path / "work",
            firmware_cache=tmp_path / "cache",
        )
        assert config.proxmox_version == "8.2"
        assert config.include_nvidia is False

    def test_directories_created(self, tmp_path):
        """Test that output/work/cache directories are created."""
        output = tmp_path / "output"
        work = tmp_path / "work"
        cache = tmp_path / "cache"

        BuildConfig(
            output_dir=output,
            work_dir=work,
            firmware_cache=cache,
        )

        assert output.exists()
        assert work.exists()
        assert cache.exists()

    def test_default_arch(self, tmp_path, monkeypatch):
        """Test that build_arch defaults to amd64 and arm64."""
        monkeypatch.chdir(tmp_path)
        config = BuildConfig()
        assert "linux/amd64" in config.build_arch
        assert "linux/arm64" in config.build_arch


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_init_no_file(self):
        """Test ConfigManager initializes without config file."""
        cm = ConfigManager()
        config = cm.get_config()
        assert config.proxmox_version == "9.1"

    def test_load_from_json(self, tmp_path, monkeypatch):
        """Test loading configuration from JSON file."""
        monkeypatch.chdir(tmp_path)
        config_data = {
            "proxmox_version": "8.1",
            "debian_release": "bookworm",
            "include_nvidia": False,
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        cm = ConfigManager(config_file)
        cm.load_from_file(config_file)
        config = cm.get_config()

        assert config.proxmox_version == "8.1"
        assert config.debian_release == "bookworm"
        assert config.include_nvidia is False

    def test_load_from_yaml(self, tmp_path, monkeypatch):
        """Test loading configuration from YAML file."""
        monkeypatch.chdir(tmp_path)
        config_data = {
            "proxmox_version": "8.0",
            "include_amd": False,
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cm = ConfigManager(config_file)
        cm.load_from_file(config_file)
        config = cm.get_config()

        assert config.proxmox_version == "8.0"
        assert config.include_amd is False

    def test_load_unsupported_format(self, tmp_path):
        """Test that unsupported file formats raise ValueError."""
        config_file = tmp_path / "config.txt"
        config_file.write_text("key=value")

        cm = ConfigManager(config_file)
        with pytest.raises(ValueError, match="Unsupported configuration format"):
            cm.load_from_file(config_file)

    def test_load_missing_file(self, tmp_path):
        """Test that missing files raise FileNotFoundError."""
        missing = tmp_path / "missing.json"
        cm = ConfigManager(missing)
        with pytest.raises(FileNotFoundError):
            cm.load_from_file(missing)

    def test_load_from_env(self, monkeypatch, tmp_path):
        """Test loading configuration from environment variables."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PROXMOX_VERSION", "7.4")
        monkeypatch.setenv("DEBIAN_RELEASE", "bullseye")
        monkeypatch.setenv("INCLUDE_NVIDIA", "false")
        monkeypatch.setenv("INCLUDE_AMD", "true")
        monkeypatch.setenv("INCLUDE_INTEL", "0")

        cm = ConfigManager()
        cm.load_from_env()
        config = cm.get_config()

        assert config.proxmox_version == "7.4"
        assert config.debian_release == "bullseye"
        assert config.include_nvidia is False
        assert config.include_amd is True
        assert config.include_intel is False

    def test_load_from_env_build_arch(self, monkeypatch, tmp_path):
        """Test BUILD_ARCH env var parsing."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("BUILD_ARCH", "linux/amd64, linux/arm64")

        cm = ConfigManager()
        cm.load_from_env()
        config = cm.get_config()

        assert config.build_arch == ["linux/amd64", "linux/arm64"]

    def test_validate_valid_config(self, tmp_path, monkeypatch):
        """Test validation passes for valid config."""
        monkeypatch.chdir(tmp_path)
        cm = ConfigManager()
        assert cm.validate() is True

    def test_validate_missing_version(self, tmp_path, monkeypatch):
        """Test validation fails when version is empty."""
        monkeypatch.chdir(tmp_path)
        cm = ConfigManager()
        cm.config.proxmox_version = ""
        with pytest.raises(ValueError, match="Proxmox version"):
            cm.validate()

    def test_validate_missing_release(self, tmp_path, monkeypatch):
        """Test validation fails when release is empty."""
        monkeypatch.chdir(tmp_path)
        cm = ConfigManager()
        cm.config.debian_release = ""
        with pytest.raises(ValueError, match="Debian release"):
            cm.validate()

    def test_validate_missing_arch(self, tmp_path, monkeypatch):
        """Test validation fails when architecture list is empty."""
        monkeypatch.chdir(tmp_path)
        cm = ConfigManager()
        cm.config.build_arch = []
        with pytest.raises(ValueError, match="architecture"):
            cm.validate()

    def test_env_overrides_file(self, tmp_path, monkeypatch):
        """Test that env vars override file config values."""
        monkeypatch.chdir(tmp_path)
        config_data = {"proxmox_version": "8.0"}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        monkeypatch.setenv("PROXMOX_VERSION", "9.2")

        cm = ConfigManager(config_file)
        cm.load_from_file(config_file)
        assert cm.get_config().proxmox_version == "8.0"

        cm.load_from_env()
        assert cm.get_config().proxmox_version == "9.2"

    def test_unknown_keys_ignored(self, tmp_path, monkeypatch):
        """Test that unknown config keys are silently ignored."""
        monkeypatch.chdir(tmp_path)
        config_data = {
            "proxmox_version": "9.1",
            "unknown_key": "value",
            "another_unknown": True,
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        cm = ConfigManager()
        cm.load_from_file(config_file)
        config = cm.get_config()
        assert config.proxmox_version == "9.1"
        assert not hasattr(config, "unknown_key")
