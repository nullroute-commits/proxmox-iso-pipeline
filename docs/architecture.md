# Architecture

> **Documentation Version:** 1.0.0  
> **Audience:** Technical Staff, System Architects  
> **Last Updated:** 2024-12-19

This document describes the system architecture, component design, and data flow of the Proxmox ISO Pipeline.

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Module Design](#module-design)
- [Docker Architecture](#docker-architecture)
- [CI/CD Pipeline](#cicd-pipeline)
- [Security Architecture](#security-architecture)

## System Overview

The Proxmox ISO Pipeline is a containerized build system that creates custom Proxmox VE installer ISOs with integrated firmware support.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Proxmox ISO Pipeline                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐    │
│  │   CLI/API    │────▶│  Builder     │────▶│  Output ISO      │    │
│  │  Interface   │     │  Engine      │     │                  │    │
│  └──────────────┘     └──────────────┘     └──────────────────┘    │
│         │                    │                                       │
│         │                    ▼                                       │
│         │            ┌──────────────┐                               │
│         │            │   Firmware   │                               │
│         └───────────▶│   Manager    │                               │
│                      └──────────────┘                               │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    External Resources                         │  │
│  │  • Proxmox ISO Repository    • Debian Package Mirrors        │  │
│  │  • firmware-linux-*          • nvidia-driver, amd-firmware   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Modularity**: Separate concerns into distinct modules
2. **Reproducibility**: Pinned versions for all dependencies
3. **Multi-Architecture**: Support for amd64 and arm64
4. **Containerization**: Docker-based isolated builds
5. **Idempotency**: Same inputs produce same outputs

## Component Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Core Components                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   │
│  │   src/builder.py │   │ src/firmware.py │   │  src/config.py  │   │
│  │                  │   │                  │   │                  │   │
│  │ • ISO Download   │   │ • Pkg Download   │   │ • YAML/JSON     │   │
│  │ • ISO Extract    │   │ • Pkg Extract    │   │ • Env Variables │   │
│  │ • ISO Rebuild    │   │ • Integration    │   │ • Validation    │   │
│  │ • Boot Config    │   │ • Verification   │   │ • Defaults      │   │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘   │
│           │                     │                     │              │
│           └─────────────────────┼─────────────────────┘              │
│                                 │                                    │
│                                 ▼                                    │
│                    ┌─────────────────────┐                          │
│                    │  ProxmoxISOBuilder  │                          │
│                    │    (Main Class)     │                          │
│                    └─────────────────────┘                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Module Responsibilities

| Module | Responsibility | Key Classes |
|--------|---------------|-------------|
| `builder.py` | ISO build orchestration | `ProxmoxISOBuilder` |
| `firmware.py` | Firmware management | `FirmwareManager` |
| `config.py` | Configuration management | `BuildConfig`, `ConfigManager` |

## Data Flow

### Build Process Flow

```
                                    START
                                      │
                                      ▼
                            ┌─────────────────┐
                            │ Load Config     │
                            │ (YAML/ENV/CLI)  │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Validate Config │
                            └────────┬────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOWNLOAD PHASE                              │
│  ┌─────────────────┐              ┌─────────────────────────┐   │
│  │ Download        │              │ Download Firmware       │   │
│  │ Proxmox ISO     │              │ Packages (apt-get)      │   │
│  │ (wget)          │              │                         │   │
│  └────────┬────────┘              └────────────┬────────────┘   │
│           │                                     │                │
└───────────┼─────────────────────────────────────┼────────────────┘
            │                                     │
            ▼                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTRACTION PHASE                            │
│  ┌─────────────────┐              ┌─────────────────────────┐   │
│  │ Mount ISO       │              │ Extract .deb Packages   │   │
│  │ Extract Files   │              │ (dpkg-deb -x)           │   │
│  │ Unmount         │              │                         │   │
│  └────────┬────────┘              └────────────┬────────────┘   │
│           │                                     │                │
└───────────┼─────────────────────────────────────┼────────────────┘
            │                                     │
            └──────────────┬──────────────────────┘
                           │
                           ▼
            ┌─────────────────────────┐
            │ INTEGRATION PHASE       │
            │                         │
            │ Copy firmware to        │
            │ ISO /firmware directory │
            └────────────┬────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │ VALIDATION PHASE        │
            │                         │
            │ • Check EFI boot files  │
            │ • Check BIOS boot files │
            │ • Verify GRUB config    │
            └────────────┬────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │ REBUILD PHASE           │
            │                         │
            │ xorriso mkisofs         │
            │ • BIOS boot (isolinux)  │
            │ • UEFI boot (efi.img)   │
            │ • Hybrid MBR/GPT        │
            └────────────┬────────────┘
                         │
                         ▼
                       FINISH
              (proxmox-ve_9.1_custom.iso)
```

### File System Layout

```
proxmox-iso-pipeline/
├── src/                          # Python source code
│   ├── __init__.py
│   ├── builder.py                # Main builder logic
│   ├── config.py                 # Configuration handling
│   └── firmware.py               # Firmware management
├── config/                       # Configuration files
│   ├── firmware-sources.json     # Firmware package definitions
│   └── preseed.cfg               # Debian preseed (future)
├── docker/                       # Docker configuration
│   ├── Dockerfile                # Multi-stage, multi-arch
│   └── entrypoint.sh             # Container entrypoint
├── scripts/                      # Shell scripts
│   ├── build-iso.sh              # Main build script
│   ├── download-firmware.sh      # Firmware download
│   └── inject-firmware.sh        # Firmware injection
├── work/                         # Working directory (gitignored)
│   ├── iso_root/                 # Extracted ISO contents
│   └── iso_mount/                # Temporary mount point
├── firmware-cache/               # Downloaded packages (gitignored)
│   ├── firmware-linux-free.deb
│   ├── nvidia-driver.deb
│   └── ...
└── output/                       # Built ISOs (gitignored)
    └── proxmox-ve_9.1_custom.iso
```

## Module Design

### builder.py - ProxmoxISOBuilder

```
┌─────────────────────────────────────────────────────────────────┐
│                     ProxmoxISOBuilder                            │
├─────────────────────────────────────────────────────────────────┤
│ Attributes:                                                      │
│   - config: BuildConfig                                          │
│   - firmware_manager: FirmwareManager                            │
│   - iso_root: Optional[Path]                                     │
├─────────────────────────────────────────────────────────────────┤
│ Methods:                                                         │
│   + download_iso(url?) -> Path                                   │
│   + extract_iso(iso_path) -> Path                                │
│   + download_firmware_packages() -> List[Path]                   │
│   + integrate_firmware(packages) -> None                         │
│   + validate_boot_files() -> bool                                │
│   + rebuild_iso(output_name?) -> Path                            │
│   + build(iso_url?) -> Path                                      │
│   - _find_mbr_template() -> Optional[Path]                       │
└─────────────────────────────────────────────────────────────────┘
```

### firmware.py - FirmwareManager

```
┌─────────────────────────────────────────────────────────────────┐
│                      FirmwareManager                             │
├─────────────────────────────────────────────────────────────────┤
│ Attributes:                                                      │
│   - cache_dir: Path                                              │
│   - debian_release: str                                          │
│   - firmware_sources: Dict[str, List[str]]                       │
│   - _sources_configured: bool                                    │
├─────────────────────────────────────────────────────────────────┤
│ Methods:                                                         │
│   + download_firmware(vendor, force?) -> List[Path]              │
│   + extract_firmware(package, dest) -> None                      │
│   + verify_checksum(file, hash, type?) -> bool                   │
│   + integrate_firmware(files, iso_root) -> None                  │
│   - _configure_apt_sources() -> None                             │
│   - _load_firmware_sources() -> Dict[str, List[str]]             │
│   - _download_package(name, force?) -> Optional[Path]            │
└─────────────────────────────────────────────────────────────────┘
```

### config.py - Configuration Classes

```
┌─────────────────────────────────────────────────────────────────┐
│                        BuildConfig                               │
├─────────────────────────────────────────────────────────────────┤
│ @dataclass                                                       │
│   - proxmox_version: str = "9.1"                                 │
│   - debian_release: str = "trixie"                               │
│   - include_nvidia: bool = True                                  │
│   - include_amd: bool = True                                     │
│   - include_intel: bool = True                                   │
│   - build_arch: List[str]                                        │
│   - output_dir: Path                                             │
│   - work_dir: Path                                               │
│   - firmware_cache: Path                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      ConfigManager                               │
├─────────────────────────────────────────────────────────────────┤
│ Attributes:                                                      │
│   - config_file: Optional[Path]                                  │
│   - config: BuildConfig                                          │
├─────────────────────────────────────────────────────────────────┤
│ Methods:                                                         │
│   + load_from_file(path) -> None                                 │
│   + load_from_env() -> None                                      │
│   + get_config() -> BuildConfig                                  │
│   + validate() -> bool                                           │
│   - _update_config(data) -> None                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Docker Architecture

### Multi-Stage Build

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dockerfile Stages                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Stage 1: base                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ debian:trixie-slim                                       │   │
│   │ + System packages (xorriso, squashfs-tools, etc.)       │   │
│   │ + Architecture-specific packages                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│   Stage 2: python-env                                            │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ FROM base                                                │   │
│   │ + Python 3.13 venv                                       │   │
│   │ + pip packages (requests, pyyaml, click, rich)          │   │
│   │ + Dev tools (flake8, black, mypy)                       │   │
│   └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│   Stage 3: builder                                               │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ FROM base                                                │   │
│   │ + COPY venv from python-env                             │   │
│   │ + Application code                                       │   │
│   │ + Build directories                                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│   Stage 4: runtime (final)                                       │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ FROM base                                                │   │
│   │ + COPY venv from python-env                             │   │
│   │ + COPY app from builder                                 │   │
│   │ + Non-root user (builder)                               │   │
│   │ + Entrypoint script                                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Architecture Support

```
┌─────────────────────────────────────────────────────────────────┐
│                  Multi-Architecture Build                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐        ┌──────────────────┐              │
│  │   linux/amd64    │        │   linux/arm64    │              │
│  │                  │        │                  │              │
│  │ + syslinux       │        │ - syslinux (N/A) │              │
│  │ + isolinux       │        │ + isolinux       │              │
│  │ + squashfs-tools │        │ + squashfs-tools │              │
│  │   (1:4.6.1-1)    │        │   (1:4.6.1-1+b1) │              │
│  └──────────────────┘        └──────────────────┘              │
│                                                                  │
│  Note: syslinux is x86-only; arm64 builds are UEFI-only        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## CI/CD Pipeline

### GitHub Actions Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                   CI/CD Pipeline Flow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Trigger: push/PR to main/develop                              │
│                      │                                           │
│                      ▼                                           │
│           ┌─────────────────┐                                   │
│           │      lint       │                                   │
│           │  • flake8       │                                   │
│           │  • pydocstyle   │                                   │
│           │  • black        │                                   │
│           │  • mypy         │                                   │
│           └────────┬────────┘                                   │
│                    │                                             │
│        ┌───────────┴───────────┐                                │
│        ▼                       ▼                                │
│ ┌──────────────┐      ┌──────────────┐                         │
│ │ build-docker │      │     test     │                         │
│ │              │      │              │                         │
│ │ • buildx     │      │ • pytest     │                         │
│ │ • multi-arch │      │ • validate   │                         │
│ │ • push ghcr  │      │   configs    │                         │
│ └──────┬───────┘      └──────────────┘                         │
│        │                                                        │
│        ▼                                                        │
│ ┌──────────────┐                                               │
│ │security-scan │                                               │
│ │              │                                               │
│ │ • Trivy      │                                               │
│ │ • SARIF      │                                               │
│ └──────┬───────┘                                               │
│        │                                                        │
│        ▼                                                        │
│ ┌──────────────┐                                               │
│ │   release    │ (main branch only)                            │
│ │              │                                               │
│ │ • Notes      │                                               │
│ │ • Artifacts  │                                               │
│ └──────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Architecture                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Layer 1: Supply Chain Security                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ • Pinned dependency versions (VERSIONS.md)              │   │
│   │ • GitHub Actions pinned to commit hashes                │   │
│   │ • Base image pinned to specific tag                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Layer 2: Container Security                                    │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ • Non-root user execution (builder:1000)                │   │
│   │ • Minimal base image (slim)                             │   │
│   │ • Limited sudo permissions                              │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Layer 3: Runtime Security                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ • Trivy vulnerability scanning                          │   │
│   │ • Read-only config mounts                               │   │
│   │ • Isolated build network                                │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Layer 4: Code Security                                         │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ • Static analysis (flake8, mypy)                        │   │
│   │ • Input validation                                      │   │
│   │ • Safe subprocess execution                             │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Privileged Operations

The builder requires elevated privileges for:

| Operation | Reason | Mitigation |
|-----------|--------|------------|
| ISO mount | Mount loop device | Targeted sudo commands |
| File copy | Root-owned files | chmod after copy |
| Package install | apt-get | Isolated container |

## Next Steps

- [API Reference](api-reference.md) - Detailed module documentation
- [Configuration Reference](configuration.md) - All options
- [Developer Guide](developer-guide.md) - Contributing

---

*[Back to Documentation Index](README.md)*
