"""Configuration management for Proxmox ISO builder."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class BuildConfig:
    """Build configuration parameters."""

    proxmox_version: str = "9.1"
    debian_release: str = "trixie"
    include_nvidia: bool = True
    include_amd: bool = True
    include_intel: bool = True
    build_arch: List[str] = None
    output_dir: Path = Path("output")
    work_dir: Path = Path("work")
    firmware_cache: Path = Path("firmware-cache")

    def __post_init__(self) -> None:
        """Initialize default values and validate configuration."""
        if self.build_arch is None:
            self.build_arch = ["linux/amd64", "linux/arm64"]

        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.firmware_cache.mkdir(parents=True, exist_ok=True)


class ConfigManager:
    """Manage configuration from multiple sources."""

    def __init__(self, config_file: Optional[Path] = None) -> None:
        """
        Initialize configuration manager.

        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file
        self.config = BuildConfig()

    def load_from_file(self, file_path: Path) -> None:
        """
        Load configuration from YAML or JSON file.

        Args:
            file_path: Path to configuration file

        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If configuration file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        suffix = file_path.suffix.lower()
        content = file_path.read_text()

        if suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
        elif suffix == ".json":
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported configuration format: {suffix}")

        self._update_config(data)

    def load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mapping = {
            "PROXMOX_VERSION": "proxmox_version",
            "DEBIAN_RELEASE": "debian_release",
            "INCLUDE_NVIDIA": "include_nvidia",
            "INCLUDE_AMD": "include_amd",
            "INCLUDE_INTEL": "include_intel",
            "BUILD_ARCH": "build_arch",
            "OUTPUT_DIR": "output_dir",
            "WORK_DIR": "work_dir",
            "FIRMWARE_CACHE": "firmware_cache",
        }

        data: Dict[str, Any] = {}
        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string to appropriate type
                if config_key in ["include_nvidia", "include_amd", "include_intel"]:
                    data[config_key] = value.lower() in ["true", "1", "yes"]
                elif config_key == "build_arch":
                    data[config_key] = [arch.strip() for arch in value.split(",")]
                elif config_key in ["output_dir", "work_dir", "firmware_cache"]:
                    data[config_key] = Path(value)
                else:
                    data[config_key] = value

        self._update_config(data)

    def _update_config(self, data: Dict[str, Any]) -> None:
        """
        Update configuration with provided data.

        Args:
            data: Dictionary containing configuration updates
        """
        for key, value in data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def get_config(self) -> BuildConfig:
        """
        Get current build configuration.

        Returns:
            BuildConfig instance with current settings
        """
        return self.config

    def validate(self) -> bool:
        """
        Validate current configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config.proxmox_version:
            raise ValueError("Proxmox version must be specified")

        if not self.config.debian_release:
            raise ValueError("Debian release must be specified")

        if not self.config.build_arch:
            raise ValueError("At least one build architecture must be specified")

        return True
