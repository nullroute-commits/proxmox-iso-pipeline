# Configuration Reference

> **Documentation Version:** 1.0.0  
> **Audience:** All Users  
> **Last Updated:** 2025-12-25

Complete reference for all configuration options available in the Proxmox ISO Pipeline.

## Table of Contents

- [Configuration Sources](#configuration-sources)
- [Environment Variables](#environment-variables)
- [Configuration File](#configuration-file)
- [CLI Options](#cli-options)
- [Firmware Sources](#firmware-sources)
- [Docker Compose Options](#docker-compose-options)
- [Default Values](#default-values)

## Configuration Sources

Configuration is loaded from multiple sources in the following priority order (highest to lowest):

1. **CLI Arguments** - Command-line options override all others
2. **Environment Variables** - Override file and defaults
3. **Configuration File** - YAML or JSON file
4. **Default Values** - Built-in defaults

### Configuration Precedence Example

```bash
# Default: proxmox_version = "9.1"

# config.yaml sets: proxmox_version: "9.0"
# Environment sets: PROXMOX_VERSION=8.3
# CLI sets: --proxmox-version 8.2

# Result: proxmox_version = "8.2" (CLI wins)
```

## Environment Variables

All environment variables and their descriptions:

### Core Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PROXMOX_VERSION` | string | `9.1` | Proxmox VE version to build |
| `DEBIAN_RELEASE` | string | `trixie` | Debian release name |

### Firmware Options

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `INCLUDE_NVIDIA` | bool | `true` | Include NVIDIA firmware |
| `INCLUDE_AMD` | bool | `true` | Include AMD firmware |
| `INCLUDE_INTEL` | bool | `true` | Include Intel firmware |

### Build Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BUILD_ARCH` | string | `linux/amd64,linux/arm64` | Comma-separated architectures |

### Directory Paths

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OUTPUT_DIR` | path | `./output` | Directory for built ISOs |
| `WORK_DIR` | path | `./work` | Working directory for builds |
| `FIRMWARE_CACHE` | path | `./firmware-cache` | Firmware package cache |

### Boolean Value Parsing

Boolean environment variables accept these values:

| True Values | False Values |
|-------------|--------------|
| `true`, `True`, `TRUE` | `false`, `False`, `FALSE` |
| `1` | `0` |
| `yes`, `Yes`, `YES` | `no`, `No`, `NO` |

### Example Usage

```bash
# Export variables
export PROXMOX_VERSION=9.1
export DEBIAN_RELEASE=trixie
export INCLUDE_NVIDIA=true
export INCLUDE_AMD=true
export INCLUDE_INTEL=true
export BUILD_ARCH=linux/amd64,linux/arm64
export OUTPUT_DIR=./output
export WORK_DIR=./work
export FIRMWARE_CACHE=./firmware-cache

# Run the build
docker compose run --rm builder build
```

## Configuration File

### YAML Format

Create `config.yaml`:

```yaml
# Proxmox ISO Pipeline Configuration
# Version: 1.0.0

# Target Proxmox version
proxmox_version: "9.1"

# Debian release name
debian_release: trixie

# Firmware inclusion options
include_nvidia: true
include_amd: true
include_intel: true

# Build architectures
build_arch:
  - linux/amd64
  - linux/arm64

# Directory paths (relative or absolute)
output_dir: ./output
work_dir: ./work
firmware_cache: ./firmware-cache
```

### JSON Format

Create `config.json`:

```json
{
  "proxmox_version": "9.1",
  "debian_release": "trixie",
  "include_nvidia": true,
  "include_amd": true,
  "include_intel": true,
  "build_arch": [
    "linux/amd64",
    "linux/arm64"
  ],
  "output_dir": "./output",
  "work_dir": "./work",
  "firmware_cache": "./firmware-cache"
}
```

### Using Configuration File

```bash
# With Python directly
python -m src.builder --config config.yaml

# With Docker Compose (mount the file)
docker compose run --rm \
  -v $(pwd)/config.yaml:/workspace/config.yaml:ro \
  builder build --config /workspace/config.yaml
```

### Configuration File Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `proxmox_version` | string | No | Proxmox VE version |
| `debian_release` | string | No | Debian release codename |
| `include_nvidia` | boolean | No | Include NVIDIA firmware |
| `include_amd` | boolean | No | Include AMD firmware |
| `include_intel` | boolean | No | Include Intel firmware |
| `build_arch` | list[string] | No | Target architectures |
| `output_dir` | string | No | Output directory path |
| `work_dir` | string | No | Working directory path |
| `firmware_cache` | string | No | Firmware cache path |

## CLI Options

### Main Command

```
proxmox-iso-build [OPTIONS]

Build custom Proxmox VE installer ISO with firmware support.
```

### Available Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--config` | `-c` | PATH | None | Configuration file path |
| `--proxmox-version` | | STRING | `9.1` | Proxmox VE version |
| `--debian-release` | | STRING | `trixie` | Debian release name |
| `--no-nvidia` | | FLAG | False | Exclude NVIDIA firmware |
| `--no-amd` | | FLAG | False | Exclude AMD firmware |
| `--no-intel` | | FLAG | False | Exclude Intel firmware |
| `--iso-url` | | STRING | None | Custom Proxmox ISO URL |
| `--help` | | FLAG | | Show help message |

### CLI Examples

```bash
# Show help
python -m src.builder --help

# Basic build with defaults
python -m src.builder

# Specify Proxmox version
python -m src.builder --proxmox-version 9.1

# Exclude specific firmware
python -m src.builder --no-nvidia --no-amd

# Use configuration file
python -m src.builder --config config.yaml

# Use custom ISO URL
python -m src.builder --iso-url https://example.com/custom.iso

# Full example with all options
python -m src.builder \
  --config config.yaml \
  --proxmox-version 9.1 \
  --debian-release trixie \
  --no-nvidia
```

### Docker Compose CLI

```bash
# Using docker compose run
docker compose run --rm builder build [OPTIONS]

# Examples
docker compose run --rm builder build
docker compose run --rm builder build --no-nvidia
docker compose run --rm builder build --proxmox-version 9.0
docker compose run --rm builder --help
```

## Firmware Sources

### Configuration File

The firmware packages are defined in `config/firmware-sources.json`:

```json
{
  "freeware": [
    "firmware-linux-free",
    "firmware-misc-nonfree",
    "firmware-linux-nonfree"
  ],
  "nvidia": [
    "nvidia-driver",
    "nvidia-kernel-dkms",
    "firmware-nvidia-graphics"
  ],
  "amd": [
    "firmware-amd-graphics",
    "amd64-microcode"
  ],
  "intel": [
    "intel-microcode",
    "firmware-intel-sound",
    "firmware-intel-graphics",
    "firmware-intel-misc"
  ]
}
```

### Vendor Categories

| Category | Always Included | Description |
|----------|-----------------|-------------|
| `freeware` | Yes | GPL and redistributable firmware |
| `nvidia` | Configurable | NVIDIA GPU drivers and firmware |
| `amd` | Configurable | AMD GPU and CPU firmware |
| `intel` | Configurable | Intel CPU and GPU firmware |

### Package Details

#### Freeware Packages

| Package | Description |
|---------|-------------|
| `firmware-linux-free` | GPL-licensed kernel firmware |
| `firmware-misc-nonfree` | Miscellaneous redistributable firmware |
| `firmware-linux-nonfree` | Additional non-free firmware |

#### NVIDIA Packages

| Package | Description |
|---------|-------------|
| `nvidia-driver` | NVIDIA proprietary graphics driver |
| `nvidia-kernel-dkms` | NVIDIA kernel module source |
| `firmware-nvidia-graphics` | NVIDIA GPU firmware |

#### AMD Packages

| Package | Description |
|---------|-------------|
| `firmware-amd-graphics` | AMD GPU (AMDGPU) firmware |
| `amd64-microcode` | AMD CPU microcode updates |

#### Intel Packages

| Package | Description |
|---------|-------------|
| `intel-microcode` | Intel CPU microcode updates |
| `firmware-intel-sound` | Intel audio DSP firmware |
| `firmware-intel-graphics` | Intel integrated graphics firmware |
| `firmware-intel-misc` | Miscellaneous Intel firmware |

### Customizing Firmware Sources

To add custom firmware:

1. Edit `config/firmware-sources.json`:

```json
{
  "freeware": [...],
  "nvidia": [...],
  "amd": [...],
  "intel": [...],
  "custom_vendor": [
    "custom-firmware-package-1",
    "custom-firmware-package-2"
  ]
}
```

2. Update `src/config.py` to add configuration option
3. Update `src/builder.py` to handle the new vendor

## Docker Compose Options

### docker-compose.yml Configuration

```yaml
version: '3.9'

services:
  builder:
    build:
      context: .
      dockerfile: docker/Dockerfile
      platforms:
        - linux/amd64
        - linux/arm64
    privileged: true  # Required for ISO mounting
    volumes:
      - ./output:/workspace/output
      - ./work:/workspace/work
      - ./firmware-cache:/workspace/firmware-cache
      - ./config:/workspace/config:ro
      - ./src:/workspace/src:ro
    environment:
      - PROXMOX_VERSION=${PROXMOX_VERSION:-9.1}
      - DEBIAN_RELEASE=${DEBIAN_RELEASE:-trixie}
      - INCLUDE_NVIDIA=${INCLUDE_NVIDIA:-true}
      - INCLUDE_AMD=${INCLUDE_AMD:-true}
      - INCLUDE_INTEL=${INCLUDE_INTEL:-true}
      - BUILD_ARCH=${BUILD_ARCH:-linux/amd64,linux/arm64}
```

### Volume Mounts

| Host Path | Container Path | Mode | Description |
|-----------|----------------|------|-------------|
| `./output` | `/workspace/output` | rw | Built ISO output |
| `./work` | `/workspace/work` | rw | Working directory |
| `./firmware-cache` | `/workspace/firmware-cache` | rw | Package cache |
| `./config` | `/workspace/config` | ro | Configuration files |
| `./src` | `/workspace/src` | ro | Source code |

### Resource Limits

Add resource limits in production:

```yaml
services:
  builder:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

## Default Values

### Complete Default Configuration

| Setting | Default Value |
|---------|---------------|
| `proxmox_version` | `9.1` |
| `debian_release` | `trixie` |
| `include_nvidia` | `true` |
| `include_amd` | `true` |
| `include_intel` | `true` |
| `build_arch` | `["linux/amd64", "linux/arm64"]` |
| `output_dir` | `./output` |
| `work_dir` | `./work` |
| `firmware_cache` | `./firmware-cache` |

### ISO Download URL

Default URL pattern:
```
https://enterprise.proxmox.com/iso/proxmox-ve_{version}-1.iso
```

Example for version 9.1:
```
https://enterprise.proxmox.com/iso/proxmox-ve_9.1-1.iso
```

## Next Steps

- [User Guide](user-guide.md) - Getting started
- [Operator Guide](operator-guide.md) - Production deployment
- [Troubleshooting](troubleshooting.md) - Common issues

---

*[Back to Documentation Index](README.md)*
