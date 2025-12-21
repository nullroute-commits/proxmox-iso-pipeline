# User Guide

> **Documentation Version:** 1.0.0  
> **Audience:** End Users  
> **Prerequisites:** Basic command line familiarity

This guide helps end users build custom Proxmox VE installer ISOs with integrated firmware support.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Building Your First ISO](#building-your-first-iso)
- [Customization Options](#customization-options)
- [Boot Modes](#boot-modes)
- [Writing to USB](#writing-to-usb)
- [Installation Tips](#installation-tips)

## Overview

The Proxmox ISO Pipeline creates custom Proxmox VE 9.1 installer ISOs based on Debian Trixie with comprehensive firmware support:

- **NVIDIA**: Graphics drivers and firmware
- **AMD**: GPU firmware and CPU microcode
- **Intel**: Microcode and graphics firmware
- **Freeware**: Linux kernel firmware packages

### Why Custom ISOs?

The standard Proxmox VE installer may lack drivers for:
- Modern NVIDIA GPUs
- Recent AMD hardware
- Specific network adapters
- Wireless cards

This pipeline integrates these drivers directly into the installer ISO.

## Prerequisites

Before you begin, ensure you have:

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| Docker | 20.10+ | With BuildKit support |
| Docker Compose | V2+ | Usually bundled with Docker Desktop |
| Disk Space | 20GB+ | For ISO building and caching |
| Internet | Stable | For downloading ISO and firmware |

### Checking Prerequisites

```bash
# Check Docker version
docker --version
# Expected: Docker version 20.10 or higher

# Check Docker Compose
docker compose version
# Expected: Docker Compose version v2.x.x

# Check available disk space
df -h .
# Ensure at least 20GB available
```

## Quick Start

The fastest way to build a custom ISO:

```bash
# 1. Clone the repository
git clone https://github.com/nullroute-commits/proxmox-iso-pipeline.git
cd proxmox-iso-pipeline

# 2. Build and run (one command)
docker compose build && docker compose run --rm builder build

# 3. Find your ISO
ls -la output/
# Output: proxmox-ve_9.1_custom.iso
```

## Building Your First ISO

### Step 1: Clone the Repository

If you haven't already, clone the repository:

```bash
git clone https://github.com/nullroute-commits/proxmox-iso-pipeline.git
cd proxmox-iso-pipeline
```

### Step 2: Build the Docker Image

```bash
docker compose build
```

This creates the builder environment with all required tools.

### Step 3: Run the Builder

```bash
# Using Docker Compose (recommended)
docker compose run --rm builder build

# Or using the convenience script
chmod +x scripts/build-iso.sh
./scripts/build-iso.sh build
```

### Step 4: Locate Your ISO

After a successful build, find your ISO in the `output/` directory:

```bash
ls -lh output/
# proxmox-ve_9.1_custom.iso
```

## Customization Options

### Firmware Selection

Control which firmware is included:

```bash
# Include all firmware (default)
docker compose run --rm builder build

# Exclude NVIDIA firmware
docker compose run --rm builder build --no-nvidia

# Exclude AMD firmware
docker compose run --rm builder build --no-amd

# Exclude Intel firmware
docker compose run --rm builder build --no-intel

# Minimal build (only freeware firmware)
docker compose run --rm builder build --no-nvidia --no-amd --no-intel
```

### Environment Variables

Set environment variables before building:

```bash
# Set Proxmox version
export PROXMOX_VERSION=9.1

# Set Debian release
export DEBIAN_RELEASE=trixie

# Control firmware inclusion
export INCLUDE_NVIDIA=true
export INCLUDE_AMD=true
export INCLUDE_INTEL=true

# Run the build
docker compose run --rm builder build
```

### Configuration File

Create a `config.yaml` for persistent settings:

```yaml
proxmox_version: "9.1"
debian_release: trixie
include_nvidia: true
include_amd: true
include_intel: true
output_dir: ./output
work_dir: ./work
firmware_cache: ./firmware-cache
```

Build with configuration file:

```bash
docker compose run --rm builder build --config config.yaml
```

## Boot Modes

The generated ISOs support multiple boot modes:

### UEFI Mode (Recommended)

- Modern systems with UEFI firmware
- **Secure Boot compatible**
- GPT partition tables
- Required for systems newer than ~2012

### Legacy BIOS Mode

- Older systems without UEFI
- MBR partition tables
- Uses isolinux bootloader

### Hybrid Boot

The ISOs are "hybrid" and support both modes:
- Automatically detected by the target system
- Works with both USB and CD/DVD boot
- Supports `dd` writing to USB devices

## Writing to USB

### Linux/macOS

```bash
# Identify your USB device
lsblk  # or 'diskutil list' on macOS

# Write ISO to USB (replace /dev/sdX with your device)
sudo dd if=output/proxmox-ve_9.1_custom.iso of=/dev/sdX bs=4M status=progress conv=fsync

# Sync to ensure write completion
sync
```

> **Warning**: Double-check the device path! Using the wrong device will destroy data.

### Windows

Use one of these tools in **DD mode** (not ISO mode):

1. **Rufus** (recommended)
   - Select "DD Image" mode when prompted
   - Download: https://rufus.ie/

2. **balenaEtcher**
   - Automatically uses DD mode
   - Download: https://etcher.balena.io/

## Installation Tips

### Pre-Installation Checklist

- [ ] Backup any existing data on the target system
- [ ] Configure BIOS/UEFI boot order to boot from USB
- [ ] Disable Secure Boot if experiencing issues (re-enable after install)
- [ ] Ensure network connectivity for post-install updates

### BIOS/UEFI Settings

1. **Boot Order**: Set USB as first boot device
2. **Secure Boot**: May need to be disabled temporarily
3. **Legacy/UEFI Mode**: Match your installation preference

### During Installation

The Proxmox installer will:
1. Detect the integrated firmware automatically
2. Load necessary drivers during installation
3. Copy firmware to the installed system

### Post-Installation

After installation, verify firmware:

```bash
# Check loaded firmware
dmesg | grep -i firmware

# Check GPU driver (NVIDIA example)
nvidia-smi

# Check CPU microcode
dmesg | grep -i microcode
```

## Common Use Cases

### Gaming/GPU Passthrough Server

```bash
# Include NVIDIA and AMD for maximum GPU support
export INCLUDE_NVIDIA=true
export INCLUDE_AMD=true
docker compose run --rm builder build
```

### Minimal Server Build

```bash
# Only basic firmware for server hardware
docker compose run --rm builder build --no-nvidia
```

### Intel-based System

```bash
# Prioritize Intel firmware
export INCLUDE_NVIDIA=false
export INCLUDE_AMD=false
export INCLUDE_INTEL=true
docker compose run --rm builder build
```

## Next Steps

- [Configuration Reference](configuration.md) - All configuration options
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Architecture](architecture.md) - Understanding how it works

---

*[Back to Documentation Index](README.md)*
