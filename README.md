# Proxmox ISO Pipeline

[![Build Status](https://github.com/nullroute-commits/proxmox-iso-pipeline/workflows/Build%20Proxmox%20ISO/badge.svg)](https://github.com/nullroute-commits/proxmox-iso-pipeline/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)
[![PEP257](https://img.shields.io/badge/docstring-pep257-green.svg)](https://www.python.org/dev/peps/pep-0257/)
[![Docker](https://img.shields.io/badge/docker-multi--arch-blue.svg)](https://www.docker.com/)

A comprehensive, multi-architecture pipeline for building custom Debian 13 (Trixie) based Proxmox VE 9.1 installer ISOs with integrated firmware support for NVIDIA, AMD, and Intel hardware.

## Features

- 🐍 **Python 3.11+** - Supports Python 3.11 through 3.13 with full PEP8 and PEP257 compliance (Docker/CI target 3.13)
- 📌 **Pinned Versions** - All dependencies pinned to latest stable versions (see [VERSIONS.md](VERSIONS.md))
- 🐳 **Docker Compose** - Multi-container orchestration for streamlined builds
- 🏗️ **Multi-Architecture** - Support for `linux/amd64`, `linux/arm64`, and `linux/loong64` (experimental)
- 📀 **Custom ISO Builder** - Automated Proxmox VE installer customization
- 🔐 **Hybrid Boot Support**:
  - ✅ UEFI/EFI boot with Secure Boot compatibility
  - ✅ Legacy BIOS boot support (isolinux)
  - ✅ Hybrid ISO format for USB/CD boot
  - ✅ GPT and MBR partition tables
- 💾 **Comprehensive Firmware Support**:
  - ✅ Freeware firmware (linux-firmware, misc-nonfree)
  - 🎮 NVIDIA proprietary drivers and firmware
  - 🔴 AMD GPU firmware and microcode
  - 🔵 Intel microcode and GPU firmware
- 🤖 **GitHub Copilot Agent** - Optimized for AI-assisted development
- ⚡ **CI/CD Pipeline** - Automated testing, linting, and multi-arch builds

## Architecture

```
┌─────────────────────────────────────────────────────┐
│            Proxmox ISO Pipeline                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐      ┌──────────────┐            │
│  │  Python 3.11+ │      │    Docker    │            │
│  │   Builder     │─────▶│   Container  │            │
│  └──────────────┘      └──────────────┘            │
│         │                      │                    │
│         ▼                      ▼                    │
│  ┌──────────────────────────────────┐              │
│  │     Firmware Integration         │              │
│  │  • NVIDIA  • AMD  • Intel        │              │
│  └──────────────────────────────────┘              │
│         │                                           │
│         ▼                                           │
│  ┌──────────────────────────────────┐              │
│  │   Multi-Arch ISO Builder         │              │
│  │   (amd64, arm64, loong64)         │              │
│  └──────────────────────────────────┘              │
│         │                                           │
│         ▼                                           │
│  ┌──────────────────────────────────┐              │
│  │   Custom Proxmox 9.1 ISO         │              │
│  └──────────────────────────────────┘              │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker 20.10+ with BuildKit support
- Docker Compose V2+
- 20GB+ free disk space
- Internet connection for downloading Proxmox ISO and firmware

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/nullroute-commits/proxmox-iso-pipeline.git
cd proxmox-iso-pipeline

# Build and run with Docker Compose
docker compose build
docker compose run --rm builder build

# Or use the convenience script
chmod +x scripts/build-iso.sh
./scripts/build-iso.sh all
```

### Using Python Directly

```bash
# Install Python 3.11+ (3.13 recommended)
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Run the builder
python -m src.builder --help
python -m src.builder --proxmox-version 9.1 --debian-release trixie
```

## Configuration

### Environment Variables

```bash
# Proxmox version
export PROXMOX_VERSION=9.1

# Debian release
export DEBIAN_RELEASE=trixie

# Firmware inclusion flags
export INCLUDE_NVIDIA=true
export INCLUDE_AMD=true
export INCLUDE_INTEL=true

# Build architecture
export BUILD_ARCH=linux/amd64,linux/arm64,linux/loong64

# Output directories
export OUTPUT_DIR=./output
export WORK_DIR=./work
export FIRMWARE_CACHE=./firmware-cache
```

### Configuration File

Create a `config.yaml`:

```yaml
proxmox_version: "9.1"
debian_release: trixie
include_nvidia: true
include_amd: true
include_intel: true
build_arch:
  - linux/amd64
  - linux/arm64
  - linux/loong64
output_dir: ./output
work_dir: ./work
firmware_cache: ./firmware-cache
```

Run with config:
```bash
python -m src.builder --config config.yaml
```

## Project Structure

```
proxmox-iso-pipeline/
├── .github/
│   ├── agent.md                  # Upstream-derived GitHub Copilot agent SoT
│   └── workflows/
│       └── build-iso.yml         # CI/CD pipeline
├── src/
│   ├── __init__.py               # Package initialization
│   ├── builder.py                # Main ISO builder (PEP8/257 compliant)
│   ├── firmware.py               # Firmware integration module
│   ├── config.py                 # Configuration management
│   └── performance.py            # Performance timing utilities
├── docker/
│   ├── Dockerfile                # Multi-stage, multi-arch Dockerfile
│   └── entrypoint.sh             # Container entrypoint script
├── scripts/
│   ├── build-iso.sh              # Main build orchestration script
│   ├── build-early-microcode.sh  # Early microcode initramfs builder
│   ├── download-firmware.sh      # Firmware download script
│   ├── inject-firmware.sh        # Firmware injection script
│   ├── rebuild-iso.sh            # ISO rebuild script
│   └── validate-tools.sh         # Tool validation script
├── config/
│   ├── preseed.cfg               # Debian preseed configuration
│   └── firmware-sources.json     # Firmware package definitions
├── tests/
│   ├── __init__.py               # Test package initialization
│   ├── conftest.py               # Pytest fixtures and shared test config
│   ├── test_builder.py           # Builder module tests
│   ├── test_config.py            # Config module tests
│   ├── test_firmware.py          # Firmware module tests
│   └── test_performance.py       # Performance module tests
├── docker-compose.yml            # Multi-service orchestration
├── pyproject.toml                # Python project configuration
├── requirements.txt              # Pinned Python dependencies
├── .flake8                       # PEP8 linting configuration
├── .gitignore                    # Git ignore patterns
├── VERSIONS.md                   # Version pinning documentation
└── README.md                     # This file
```

## Usage Examples

### Basic Build

```bash
# Build with default settings (all firmware included)
docker compose run --rm builder build

# Check help
docker compose run --rm builder --help
```

### Custom Build

```bash
# Build without NVIDIA firmware
docker compose run --rm builder build --no-nvidia

# Build with specific Proxmox version
docker compose run --rm builder build --proxmox-version 9.0

# Build with custom ISO URL
docker compose run --rm builder build --iso-url https://example.com/custom.iso
```

### Code Quality Checks

```bash
# Run linting
docker compose run --rm linter

# Or manually
flake8 src/
pydocstyle src/
black --check src/
```

### Multi-Architecture Build

```bash
# Build for specific architecture
docker buildx build --platform linux/amd64 -f docker/Dockerfile .

# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -f docker/Dockerfile .

# Build with loong64 (experimental, requires compatible base image)
docker buildx build --platform linux/amd64,linux/arm64,linux/loong64 -f docker/Dockerfile .
```

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/nullroute-commits/proxmox-iso-pipeline.git
cd proxmox-iso-pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Code Standards

This project strictly adheres to:
- **PEP 8**: Python code style guide
- **PEP 257**: Docstring conventions
- **Type hints**: All functions include type annotations
- **Black**: Code formatting (88 character line length)

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_builder.py -v
```

### Adding New Firmware

1. Edit `config/firmware-sources.json`:
```json
{
  "custom_vendor": [
    "package-name-1",
    "package-name-2"
  ]
}
```

2. Update `src/firmware.py` if needed
3. Test the changes
4. Update documentation

## Version Management

All software dependencies are pinned to specific stable versions to ensure reproducible builds and security. See [VERSIONS.md](VERSIONS.md) for the complete list of pinned versions and update procedures.

### Updating Dependencies

```bash
# Check for outdated Python packages
pip list --outdated

# Update versions in pyproject.toml and requirements.txt
# Always test before committing

# Update system packages in Dockerfile
# Check Debian package versions
apt-cache policy <package-name>
```

## GitHub Copilot Integration

This project includes an upstream-derived GitHub Copilot agent configuration in `.github/agent.md`.

The file is the project-scoped overlay for the upstream [`nullroute-commits/agency-agents`](https://github.com/nullroute-commits/agency-agents) GitHub Copilot skill set, primarily combining the `DevOps Automator` and `Backend Architect` roles with repository-specific operating facts.

The agent is optimized for:

- Understanding the build pipeline architecture
- Assisting with Python 3.13 development
- Managing Docker and multi-arch builds
- Firmware integration tasks
- Maintaining PEP8/PEP257 compliance
- Keeping repository-specific guidance aligned with the upstream agency-agents source of truth

To use the agent, ensure GitHub Copilot is enabled in your IDE and reference `.github/agent.md` as the repository skill and source of truth.

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/build-iso.yml`) provides:

1. **Linting**: PEP8, PEP257, Black, mypy checks
2. **Dockerfile & Shell Lint**: Hadolint, ShellCheck
3. **Multi-arch Build**: Docker image for amd64 and arm64 (loong64 when base image available)
4. **Testing**: Pytest execution with coverage (66 tests, ~60% coverage)
5. **Security Scanning**: Trivy vulnerability scanning
6. **Release**: Automated release creation on main branch

### Triggering Builds

```bash
# Push to trigger CI
git push origin main

# Manual workflow dispatch
# Go to Actions tab → Build Proxmox ISO → Run workflow
```

## Firmware Details

### Freeware Firmware
- `firmware-linux-free` - GPL-licensed firmware
- `firmware-misc-nonfree` - Redistributable non-free firmware
- `firmware-linux-nonfree` - Additional non-free firmware

### Proprietary Firmware

#### NVIDIA
- `nvidia-driver` - NVIDIA graphics driver
- `nvidia-kernel-dkms` - NVIDIA kernel modules
- `firmware-nvidia-graphics` - NVIDIA GPU firmware

#### AMD
- `firmware-amd-graphics` - AMD GPU firmware
- `amd64-microcode` - AMD CPU microcode updates

#### Intel
- `intel-microcode` - Intel CPU microcode updates
- `firmware-intel-sound` - Intel audio firmware
- `firmware-intel-graphics` - Intel integrated graphics firmware
- `firmware-intel-misc` - Miscellaneous Intel firmware

## Boot Compatibility

### Secure Boot Support

The generated ISOs are fully compatible with UEFI Secure Boot:

- **EFI Boot**: Uses signed GRUB2 bootloader (grubx64.efi) compatible with Secure Boot
- **Boot Image**: Includes efi.img with proper EFI System Partition (ESP) structure
- **Validation**: Automatically validates boot files before ISO creation

### Hybrid Boot Mode

The ISOs support multiple boot modes for maximum compatibility:

1. **UEFI Mode** (Secure Boot compatible)
   - Modern systems with UEFI firmware
   - Secure Boot enabled systems
   - GPT-partitioned disks

2. **Legacy BIOS Mode**
   - Older systems without UEFI
   - MBR-partitioned disks
   - Uses isolinux bootloader

3. **Hybrid USB Boot**
   - Works as both UEFI and BIOS bootable USB
   - Includes both MBR and GPT partition tables
   - Supports dd writing to USB devices

### Boot Verification

The build process automatically:
- Validates presence of efi.img for UEFI boot
- Checks for isolinux.bin for BIOS boot
- Verifies GRUB configuration files
- Logs available boot modes

## Troubleshooting

### Build Fails with "Permission Denied"

The container needs specific capabilities for ISO mounting:
```bash
docker compose run --rm builder build
```

The compose file already includes `cap_add: SYS_ADMIN, MKNOD` which is required for mount operations.

### Firmware Download Fails

Check your internet connection and Debian repository availability:
```bash
curl -I http://deb.debian.org/debian/
```

### ISO Too Large

Reduce firmware inclusion:
```bash
docker compose run --rm builder build --no-nvidia --no-amd
```

### Multi-arch Build Issues

Ensure QEMU is properly set up:
```bash
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

### ISO Won't Boot

If the generated ISO fails to boot:

1. **Check boot mode**: Ensure your system supports the boot mode (UEFI vs BIOS)
2. **Verify Secure Boot**: On Secure Boot systems, ensure the ISO has EFI boot support
3. **USB Boot**: Use proper USB writing tools:
   ```bash
   # Linux/macOS
   sudo dd if=proxmox-ve_9.1_custom.iso of=/dev/sdX bs=4M status=progress
   
   # Windows - use Rufus or similar tool in DD mode
   ```
4. **Check logs**: Review build logs for boot validation warnings
5. **Test in VM**: Verify ISO boots in both UEFI and BIOS modes using QEMU:
   ```bash
   # UEFI mode
   qemu-system-x86_64 -bios /usr/share/ovmf/OVMF.fd -cdrom output/proxmox-ve_9.1_custom.iso -m 4G
   
   # BIOS mode
   qemu-system-x86_64 -cdrom output/proxmox-ve_9.1_custom.iso -m 4G
   ```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Ensure code passes all linting checks
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Proxmox VE team for the excellent virtualization platform
- Debian project for the stable base system
- Docker community for containerization tools

## Documentation

For comprehensive documentation, see the [docs/](docs/) directory:

- 📖 [Documentation Index](docs/README.md) - Start here
- 👤 [User Guide](docs/user-guide.md) - Getting started and basic usage
- 🔧 [Operator Guide](docs/operator-guide.md) - Deployment and CI/CD
- 💻 [Developer Guide](docs/developer-guide.md) - Contributing
- 🏗️ [Architecture](docs/architecture.md) - System design
- ⚙️ [Configuration Reference](docs/configuration.md) - All options
- 🔍 [Troubleshooting](docs/troubleshooting.md) - Common issues
- 📚 [API Reference](docs/api-reference.md) - Python API

## Support

- 📖 Documentation: [docs/](docs/README.md)
- 🐛 Issues: [GitHub Issues](https://github.com/nullroute-commits/proxmox-iso-pipeline/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/nullroute-commits/proxmox-iso-pipeline/discussions)

---

**Built with ❤️ for the Proxmox community**
