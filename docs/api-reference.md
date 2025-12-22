# API Reference

> **Documentation Version:** 1.0.0  
> **Audience:** Developers  
> **Last Updated:** 2024-12-19

Python API documentation for the Proxmox ISO Pipeline modules.

## Table of Contents

- [Module Overview](#module-overview)
- [src.builder](#srcbuilder)
- [src.firmware](#srcfirmware)
- [src.config](#srcconfig)
- [src.performance](#srcperformance)
- [Exceptions](#exceptions)
- [Type Definitions](#type-definitions)

## Module Overview

```
src/
├── __init__.py      # Package initialization
├── builder.py       # Main ISO builder logic
├── firmware.py      # Firmware download and integration
├── config.py        # Configuration management
└── performance.py   # Performance timing utilities
```

### Import Examples

```python
# Import main builder
from src.builder import ProxmoxISOBuilder

# Import firmware manager
from src.firmware import FirmwareManager, FirmwareError

# Import configuration
from src.config import BuildConfig, ConfigManager

# Import performance utilities
from src.performance import (
    PerformanceTracker,
    track_performance,
    get_performance_tracker,
)
```

## src.builder

Main ISO builder module for Proxmox installer customization.

### Class: ProxmoxISOBuilder

```python
class ProxmoxISOBuilder:
    """Build custom Proxmox VE installer ISO with firmware."""
```

#### Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `PROXMOX_ISO_BASE_URL` | `str` | URL template for Proxmox ISO downloads |

#### Constructor

```python
def __init__(self, config: BuildConfig) -> None:
    """
    Initialize Proxmox ISO builder.

    Args:
        config: Build configuration instance

    Example:
        >>> from src.config import BuildConfig
        >>> from src.builder import ProxmoxISOBuilder
        >>> config = BuildConfig(proxmox_version="9.1")
        >>> builder = ProxmoxISOBuilder(config)
    """
```

#### Methods

##### download_iso

```python
def download_iso(self, url: Optional[str] = None) -> Path:
    """
    Download Proxmox VE ISO.

    Args:
        url: Optional custom ISO URL. If None, uses default Proxmox URL.

    Returns:
        Path to downloaded ISO file.

    Raises:
        RuntimeError: If download fails.

    Example:
        >>> iso_path = builder.download_iso()
        >>> print(iso_path)
        PosixPath('work/proxmox-ve_9.1.iso')

        >>> custom_iso = builder.download_iso("https://example.com/custom.iso")
    """
```

##### extract_iso

```python
def extract_iso(self, iso_path: Path) -> Path:
    """
    Extract ISO contents to working directory.

    Args:
        iso_path: Path to ISO file to extract.

    Returns:
        Path to extracted ISO root directory.

    Raises:
        RuntimeError: If extraction fails (mount/copy errors).

    Note:
        Requires sudo privileges for mount operations.

    Example:
        >>> iso_path = Path("work/proxmox-ve_9.1.iso")
        >>> iso_root = builder.extract_iso(iso_path)
        >>> print(iso_root)
        PosixPath('work/iso_root')
    """
```

##### download_firmware_packages

```python
def download_firmware_packages(self) -> List[Path]:
    """
    Download all required firmware packages.

    Downloads firmware based on configuration:
    - Always downloads freeware firmware
    - Downloads NVIDIA if config.include_nvidia is True
    - Downloads AMD if config.include_amd is True
    - Downloads Intel if config.include_intel is True

    Returns:
        List of downloaded firmware package paths.

    Example:
        >>> packages = builder.download_firmware_packages()
        >>> print(len(packages))
        12
        >>> print(packages[0])
        PosixPath('firmware-cache/firmware-linux-free.deb')
    """
```

##### integrate_firmware

```python
def integrate_firmware(self, firmware_packages: List[Path]) -> None:
    """
    Integrate firmware packages into extracted ISO.

    Args:
        firmware_packages: List of firmware package paths to integrate.

    Raises:
        RuntimeError: If ISO root is not set (extract_iso not called).

    Example:
        >>> packages = builder.download_firmware_packages()
        >>> builder.integrate_firmware(packages)
    """
```

##### validate_boot_files

```python
def validate_boot_files(self) -> bool:
    """
    Validate that required boot files exist in the ISO.

    Checks for:
    - EFI boot image (efi.img) - required
    - BIOS boot files (isolinux.bin) - optional
    - GRUB configuration files - optional

    Returns:
        True if all required boot files exist.

    Raises:
        RuntimeError: If ISO root is not set or required files missing.

    Example:
        >>> is_valid = builder.validate_boot_files()
        >>> print(is_valid)
        True
    """
```

##### rebuild_iso

```python
def rebuild_iso(self, output_name: Optional[str] = None) -> Path:
    """
    Rebuild ISO from modified contents with hybrid BIOS/UEFI boot support.

    Creates a bootable ISO that supports:
    - UEFI boot (including Secure Boot compatibility)
    - Legacy BIOS boot (via isolinux)
    - USB/hybrid boot modes

    Args:
        output_name: Optional custom output ISO filename.

    Returns:
        Path to created ISO file.

    Raises:
        RuntimeError: If ISO root is not set or rebuild fails.

    Example:
        >>> output_iso = builder.rebuild_iso()
        >>> print(output_iso)
        PosixPath('output/proxmox-ve_9.1_custom.iso')

        >>> custom_output = builder.rebuild_iso("my-custom-proxmox.iso")
    """
```

##### build

```python
def build(self, iso_url: Optional[str] = None) -> Path:
    """
    Execute complete ISO build process.

    Orchestrates the full build pipeline:
    1. Download original ISO
    2. Extract ISO contents
    3. Download firmware packages
    4. Integrate firmware
    5. Rebuild ISO

    Args:
        iso_url: Optional custom Proxmox ISO URL.

    Returns:
        Path to created custom ISO.

    Example:
        >>> output_iso = builder.build()
        >>> print(output_iso)
        PosixPath('output/proxmox-ve_9.1_custom.iso')
    """
```

### Function: main

```python
@click.command()
def main(
    config: Optional[Path],
    proxmox_version: str,
    debian_release: str,
    no_nvidia: bool,
    no_amd: bool,
    no_intel: bool,
    iso_url: Optional[str],
) -> None:
    """
    CLI entry point for building custom Proxmox VE installer ISO.

    This function is decorated with Click options and serves as the
    command-line interface entry point.
    """
```

## src.firmware

Firmware integration module for managing firmware downloads and ISO integration.

### Class: FirmwarePackage

```python
@dataclass
class FirmwarePackage:
    """
    Firmware package information.

    Attributes:
        name: Package name
        vendor: Hardware vendor (nvidia, amd, intel, freeware)
        version: Package version string
        url: Download URL
        checksum: Optional package checksum
        checksum_type: Hash algorithm (default: sha256)
    """
    name: str
    vendor: str
    version: str
    url: str
    checksum: Optional[str] = None
    checksum_type: str = "sha256"
```

### Class: FirmwareManager

```python
class FirmwareManager:
    """Manage firmware download and integration."""
```

#### Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `DEBIAN_REPO_BASE` | `str` | Base URL for Debian repositories |
| `FIRMWARE_SOURCES_FILE` | `str` | Path to firmware sources config |

#### Constructor

```python
def __init__(self, cache_dir: Path, debian_release: str = "trixie") -> None:
    """
    Initialize firmware manager.

    Args:
        cache_dir: Directory for caching firmware packages.
        debian_release: Debian release name (default: trixie).

    Example:
        >>> from pathlib import Path
        >>> fm = FirmwareManager(Path("./firmware-cache"), "trixie")
    """
```

#### Methods

##### download_firmware

```python
def download_firmware(self, vendor: str, force: bool = False) -> List[Path]:
    """
    Download firmware packages for specified vendor.

    Args:
        vendor: Hardware vendor name. One of:
            - "freeware": Free/redistributable firmware
            - "nvidia": NVIDIA GPU firmware
            - "amd": AMD GPU/CPU firmware
            - "intel": Intel CPU/GPU firmware
        force: Force re-download even if cached.

    Returns:
        List of paths to downloaded firmware packages.

    Raises:
        FirmwareDownloadError: If vendor unknown or download fails.

    Example:
        >>> packages = fm.download_firmware("nvidia")
        >>> print(packages)
        [PosixPath('firmware-cache/nvidia-driver.deb'), ...]

        >>> packages = fm.download_firmware("freeware", force=True)
    """
```

##### extract_firmware

```python
def extract_firmware(self, package_path: Path, dest_dir: Path) -> None:
    """
    Extract firmware files from Debian package.

    Args:
        package_path: Path to .deb package file.
        dest_dir: Destination directory for extracted files.

    Raises:
        FirmwareIntegrationError: If extraction fails.

    Example:
        >>> fm.extract_firmware(
        ...     Path("firmware-cache/nvidia-driver.deb"),
        ...     Path("work/extract")
        ... )
    """
```

##### verify_checksum

```python
def verify_checksum(
    self,
    file_path: Path,
    expected_hash: str,
    hash_type: str = "sha256"
) -> bool:
    """
    Verify file checksum.

    Args:
        file_path: Path to file to verify.
        expected_hash: Expected hash value.
        hash_type: Hash algorithm ("sha256" or "md5").

    Returns:
        True if checksum matches, False otherwise.

    Raises:
        ValueError: If unsupported hash type.

    Example:
        >>> is_valid = fm.verify_checksum(
        ...     Path("firmware.deb"),
        ...     "abc123...",
        ...     "sha256"
        ... )
    """
```

##### integrate_firmware

```python
def integrate_firmware(
    self,
    firmware_files: List[Path],
    iso_root: Path
) -> None:
    """
    Integrate firmware files into ISO root.

    Extracts firmware packages and copies firmware files
    to the ISO's /firmware directory.

    Args:
        firmware_files: List of firmware package paths.
        iso_root: Root directory of extracted ISO.

    Raises:
        FirmwareIntegrationError: If integration fails.

    Example:
        >>> packages = fm.download_firmware("nvidia")
        >>> fm.integrate_firmware(packages, Path("work/iso_root"))
    """
```

## src.config

Configuration management module for handling build settings.

### Class: BuildConfig

```python
@dataclass
class BuildConfig:
    """
    Build configuration parameters.

    Attributes:
        proxmox_version: Proxmox VE version (default: "9.1")
        debian_release: Debian release name (default: "trixie")
        include_nvidia: Include NVIDIA firmware (default: True)
        include_amd: Include AMD firmware (default: True)
        include_intel: Include Intel firmware (default: True)
        build_arch: Target architectures (default: amd64, arm64)
        output_dir: Output directory for ISOs
        work_dir: Working directory for builds
        firmware_cache: Firmware package cache directory
    """
    proxmox_version: str = "9.1"
    debian_release: str = "trixie"
    include_nvidia: bool = True
    include_amd: bool = True
    include_intel: bool = True
    build_arch: Optional[List[str]] = None
    output_dir: Path = Path("output")
    work_dir: Path = Path("work")
    firmware_cache: Path = Path("firmware-cache")
```

#### Example Usage

```python
from src.config import BuildConfig
from pathlib import Path

# Create with defaults
config = BuildConfig()

# Create with custom values
config = BuildConfig(
    proxmox_version="9.1",
    debian_release="trixie",
    include_nvidia=True,
    include_amd=False,
    include_intel=True,
    output_dir=Path("/data/output"),
    work_dir=Path("/data/work"),
    firmware_cache=Path("/data/cache")
)
```

### Class: ConfigManager

```python
class ConfigManager:
    """Manage configuration from multiple sources."""
```

#### Constructor

```python
def __init__(self, config_file: Optional[Path] = None) -> None:
    """
    Initialize configuration manager.

    Args:
        config_file: Optional path to configuration file.

    Example:
        >>> cm = ConfigManager()
        >>> cm = ConfigManager(Path("config.yaml"))
    """
```

#### Methods

##### load_from_file

```python
def load_from_file(self, file_path: Path) -> None:
    """
    Load configuration from YAML or JSON file.

    Args:
        file_path: Path to configuration file.

    Raises:
        FileNotFoundError: If configuration file doesn't exist.
        ValueError: If file format is not supported.

    Example:
        >>> cm = ConfigManager()
        >>> cm.load_from_file(Path("config.yaml"))
    """
```

##### load_from_env

```python
def load_from_env(self) -> None:
    """
    Load configuration from environment variables.

    Environment variable mapping:
    - PROXMOX_VERSION -> proxmox_version
    - DEBIAN_RELEASE -> debian_release
    - INCLUDE_NVIDIA -> include_nvidia
    - INCLUDE_AMD -> include_amd
    - INCLUDE_INTEL -> include_intel
    - BUILD_ARCH -> build_arch (comma-separated)
    - OUTPUT_DIR -> output_dir
    - WORK_DIR -> work_dir
    - FIRMWARE_CACHE -> firmware_cache

    Example:
        >>> import os
        >>> os.environ["PROXMOX_VERSION"] = "9.1"
        >>> cm = ConfigManager()
        >>> cm.load_from_env()
    """
```

##### get_config

```python
def get_config(self) -> BuildConfig:
    """
    Get current build configuration.

    Returns:
        BuildConfig instance with current settings.

    Example:
        >>> cm = ConfigManager()
        >>> config = cm.get_config()
        >>> print(config.proxmox_version)
        '9.1'
    """
```

##### validate

```python
def validate(self) -> bool:
    """
    Validate current configuration.

    Returns:
        True if configuration is valid.

    Raises:
        ValueError: If configuration is invalid.

    Example:
        >>> cm = ConfigManager()
        >>> is_valid = cm.validate()
        >>> print(is_valid)
        True
    """
```

## src.performance

Performance timing utilities for tracking build stages and actions.

### Class: TimingRecord

```python
@dataclass
class TimingRecord:
    """
    Record of a single timed operation.

    Attributes:
        name: Name of the operation being timed
        stage: Stage category for the operation
        start_time: Unix timestamp when timing started
        end_time: Unix timestamp when timing ended (None if still running)
        duration: Duration in seconds (None if still running)
    """
    name: str
    stage: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None

    def complete(self) -> None:
        """Mark the timing record as complete."""
```

### Class: PerformanceTracker

```python
class PerformanceTracker:
    """Track and report performance metrics for build stages and actions."""
```

#### Constructor

```python
def __init__(self) -> None:
    """
    Initialize performance tracker.

    Example:
        >>> from src.performance import PerformanceTracker
        >>> tracker = PerformanceTracker()
    """
```

#### Methods

##### start_timer

```python
def start_timer(self, name: str, stage: str = "default") -> TimingRecord:
    """
    Start a timer for a named operation.

    Args:
        name: Name of the operation being timed.
        stage: Stage category for the operation.

    Returns:
        TimingRecord for the started timer.

    Example:
        >>> record = tracker.start_timer("download_iso", "download")
    """
```

##### stop_timer

```python
def stop_timer(self, name: str, stage: str = "default") -> Optional[TimingRecord]:
    """
    Stop a timer for a named operation.

    Args:
        name: Name of the operation.
        stage: Stage category for the operation.

    Returns:
        Completed TimingRecord or None if timer not found.

    Example:
        >>> record = tracker.stop_timer("download_iso", "download")
        >>> print(record.duration)
        45.23
    """
```

##### track (context manager)

```python
@contextmanager
def track(
    self, name: str, stage: str = "default"
) -> Generator[TimingRecord, None, None]:
    """
    Context manager for tracking execution time of an operation.

    Args:
        name: Name of the operation being timed.
        stage: Stage category for the operation.

    Yields:
        TimingRecord for the operation.

    Example:
        >>> with tracker.track("extract_iso", "extract") as record:
        ...     # perform extraction
        ...     pass
        >>> print(record.duration)
        12.5
    """
```

##### get_stage_summary

```python
def get_stage_summary(self) -> Dict[str, float]:
    """
    Get total time spent in each stage.

    Returns:
        Dictionary mapping stage names to total duration in seconds.

    Example:
        >>> summary = tracker.get_stage_summary()
        >>> print(summary)
        {'download': 45.2, 'extract': 12.5, 'firmware': 30.1}
    """
```

##### get_total_time

```python
def get_total_time(self) -> float:
    """
    Get total time for all recorded operations.

    Returns:
        Total duration in seconds.

    Example:
        >>> total = tracker.get_total_time()
        >>> print(f"Total: {total:.2f}s")
        Total: 87.80s
    """
```

##### format_duration

```python
def format_duration(self, seconds: float) -> str:
    """
    Format duration in human-readable format.

    Converts seconds into a human-readable string with appropriate
    units (seconds, minutes, hours).

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted duration string.

    Example:
        >>> tracker.format_duration(45.5)
        '45.50s'
        >>> tracker.format_duration(125.3)
        '2m 5.30s'
        >>> tracker.format_duration(3725.5)
        '1h 2m 5.50s'
    """
```

##### print_summary

```python
def print_summary(self, console: Optional[Console] = None) -> None:
    """
    Print a summary table of all timing records.

    Args:
        console: Rich console for output (creates new one if not provided).

    Example:
        >>> tracker.print_summary()
        # Prints formatted performance table
    """
```

##### to_dict

```python
def to_dict(self) -> Dict:
    """
    Export timing data as a dictionary.

    Returns:
        Dictionary containing all timing records and summaries.

    Example:
        >>> data = tracker.to_dict()
        >>> print(data["total_time"])
        87.8
    """
```

### Global Functions

##### get_performance_tracker

```python
def get_performance_tracker() -> PerformanceTracker:
    """
    Get the global performance tracker instance.

    Returns:
        Global PerformanceTracker instance.

    Example:
        >>> tracker = get_performance_tracker()
    """
```

##### reset_performance_tracker

```python
def reset_performance_tracker() -> None:
    """
    Reset the global performance tracker.

    Example:
        >>> reset_performance_tracker()
    """
```

##### track_performance (context manager)

```python
@contextmanager
def track_performance(
    name: str, stage: str = "default"
) -> Generator[TimingRecord, None, None]:
    """
    Convenience context manager for tracking performance.

    Uses the global performance tracker.

    Args:
        name: Name of the operation being timed.
        stage: Stage category for the operation.

    Yields:
        TimingRecord for the operation.

    Example:
        >>> from src.performance import track_performance
        >>> with track_performance("download_iso", "download"):
        ...     # perform download
        ...     pass
    """
```

## Exceptions

### FirmwareError

```python
class FirmwareError(Exception):
    """Base exception for firmware operations."""
    pass
```

### FirmwareDownloadError

```python
class FirmwareDownloadError(FirmwareError):
    """
    Exception raised when firmware download fails.

    Example:
        >>> raise FirmwareDownloadError("Package not found: nvidia-driver")
    """
    pass
```

### FirmwareIntegrationError

```python
class FirmwareIntegrationError(FirmwareError):
    """
    Exception raised when firmware integration fails.

    Example:
        >>> raise FirmwareIntegrationError("Failed to extract package")
    """
    pass
```

## Type Definitions

### Common Types

```python
from pathlib import Path
from typing import List, Optional, Dict, Any

# Path types
PathLike = Path | str

# Configuration types
FirmwareSources = Dict[str, List[str]]
ConfigData = Dict[str, Any]

# Return types
PackageList = List[Path]
```

### Type Annotations in Functions

```python
# Function with full type annotations
def download_firmware(
    vendor: str,
    force: bool = False
) -> List[Path]:
    ...

# Method returning optional value
def _download_package(
    self,
    package_name: str,
    force: bool = False
) -> Optional[Path]:
    ...
```

## Usage Examples

### Complete Build Example

```python
from pathlib import Path
from src.config import BuildConfig, ConfigManager
from src.builder import ProxmoxISOBuilder

# Method 1: Direct configuration
config = BuildConfig(
    proxmox_version="9.1",
    include_nvidia=True,
    include_amd=True,
    include_intel=True,
)

builder = ProxmoxISOBuilder(config)
output_iso = builder.build()
print(f"ISO created: {output_iso}")

# Method 2: Using ConfigManager
cm = ConfigManager()
cm.load_from_file(Path("config.yaml"))
cm.load_from_env()  # Override with env vars
cm.validate()

builder = ProxmoxISOBuilder(cm.get_config())
output_iso = builder.build()
```

### Custom Firmware Integration

```python
from pathlib import Path
from src.firmware import FirmwareManager

# Initialize manager
fm = FirmwareManager(Path("./firmware-cache"), "trixie")

# Download specific vendor firmware
nvidia_packages = fm.download_firmware("nvidia")
amd_packages = fm.download_firmware("amd")

# Integrate into ISO
all_packages = nvidia_packages + amd_packages
fm.integrate_firmware(all_packages, Path("./work/iso_root"))
```

## Next Steps

- [Developer Guide](developer-guide.md) - Contributing
- [Architecture](architecture.md) - System design
- [Configuration Reference](configuration.md) - All options

---

*[Back to Documentation Index](README.md)*
