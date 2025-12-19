# Version Pinning Documentation

This document tracks all pinned versions used in the Proxmox ISO Pipeline project.

## Last Updated
2024-12-19

## Python Runtime
- **Python**: 3.13.0
  - Specified in: `pyproject.toml`, `Dockerfile`, GitHub Actions

## Python Dependencies

### Core Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| requests | 2.32.3 | HTTP library for downloading files |
| pyyaml | 6.0.2 | YAML configuration parsing |
| click | 8.1.7 | CLI framework |
| rich | 13.9.4 | Terminal formatting and progress bars |
| python-debian | 0.1.49 | Debian package handling |

### Development Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| flake8 | 7.1.1 | PEP8 linting |
| pydocstyle | 6.3.0 | PEP257 docstring validation |
| black | 24.10.0 | Code formatting |
| mypy | 1.13.0 | Type checking |
| pytest | 8.3.4 | Testing framework |
| pytest-cov | 6.0.0 | Coverage reporting |

### Build Tools
| Package | Version | Purpose |
|---------|---------|---------|
| pip | 24.3.1 | Package installer |
| setuptools | 75.6.0 | Package builder |
| wheel | 0.45.0 | Wheel package support |

## System Packages (Debian Trixie)

### Base Image
- **debian**: trixie-20241202-slim

### System Dependencies
Packages installed without version pinning to support multi-architecture builds (amd64 and arm64).
Package versions may vary between architectures.

| Package | Purpose | Architecture |
|---------|---------|--------------|
| python3.13 | Python runtime | all |
| python3.13-venv | Virtual environment support | all |
| python3-pip | Python package installer | all |
| wget | File downloader | all |
| curl | Transfer tool | all |
| xorriso | ISO image creator | all |
| isolinux | Boot loader | all |
| genisoimage | ISO creation tool | all |
| squashfs-tools | SquashFS filesystem tools | all |
| sudo | Privilege escalation | all |
| ca-certificates | SSL certificates | all |
| gnupg | GPG encryption | all |
| syslinux | Boot loader suite (legacy BIOS) | amd64 only |
| syslinux-utils | Syslinux utilities | amd64 only |

**Note**: `syslinux` and `syslinux-utils` are x86-specific packages required for legacy BIOS boot support.
They are not available on ARM64 architecture and are conditionally installed only on amd64 builds.

## GitHub Actions

### Actions
| Action | Version | Purpose |
|--------|---------|---------|
| actions/checkout | v6.0.1 | Repository checkout |
| actions/setup-python | v6.1.0 | Python environment setup |
| docker/setup-qemu-action | v3.7.0 | QEMU emulation for multi-arch |
| docker/setup-buildx-action | v3.12.0 | Docker Buildx setup |
| docker/login-action | v3.6.0 | Docker registry login |
| docker/metadata-action | v5.10.0 | Docker metadata extraction |
| docker/build-push-action | v6.18.0 | Docker image build/push |
| aquasecurity/trivy-action | 0.33.1 | Security vulnerability scanning |
| github/codeql-action/upload-sarif | v4.31.9 | CodeQL SARIF upload |

## Docker

### Docker Compose
- **Version**: 3.9 (Compose file format)

### Docker Image Tags
- Base: `debian:trixie-20241202-slim`
- Builder: `proxmox-iso-builder:latest`

## Target Software Versions

### Proxmox VE
- **Default Version**: 9.1
- Configurable via `PROXMOX_VERSION` environment variable

### Debian Release
- **Default Release**: Trixie (Debian 13)
- Configurable via `DEBIAN_RELEASE` environment variable

## Firmware Packages

Firmware packages are downloaded from Debian repositories and versions are determined by the Debian Trixie release at build time.

### Freeware Firmware
- firmware-linux-free
- firmware-misc-nonfree
- firmware-linux-nonfree

### Proprietary Firmware
- **NVIDIA**: nvidia-driver, nvidia-kernel-dkms, firmware-nvidia-graphics
- **AMD**: firmware-amd-graphics, amd64-microcode, firmware-amd-microcode
- **Intel**: intel-microcode, firmware-intel-sound, firmware-intelwimax, i915-firmware

## Version Update Process

### When to Update
- Monthly security reviews
- When critical vulnerabilities are discovered
- Before major releases
- After testing new versions in development

### How to Update

1. **Python Dependencies**
   ```bash
   # Check for updates
   pip list --outdated
   
   # Update pyproject.toml and requirements.txt
   # Test thoroughly before committing
   ```

2. **System Packages**
   ```bash
   # Check Debian package versions
   apt-cache policy <package-name>
   
   # Update Dockerfile with new versions
   ```

3. **GitHub Actions**
   - Visit each action's repository
   - Check latest release tags
   - Update `.github/workflows/build-iso.yml`

4. **Testing After Updates**
   ```bash
   # Run linting
   ./scripts/build-iso.sh lint
   
   # Build Docker image
   ./scripts/build-iso.sh build-image
   
   # Run full build test
   ./scripts/build-iso.sh build
   ```

## Security Considerations

- Python package versions are pinned to prevent supply chain attacks
- System packages use latest versions from stable Debian Trixie repositories
- Regular security scans with Trivy
- Dependencies are reviewed before updates
- Critical security patches are applied immediately

## Maintenance Schedule

- **Weekly**: Check for security advisories
- **Monthly**: Review dependency updates
- **Quarterly**: Major version updates and testing
- **Annually**: Complete dependency audit

## References

- Python Package Index: https://pypi.org/
- Debian Packages: https://packages.debian.org/
- GitHub Actions Marketplace: https://github.com/marketplace?type=actions
- Docker Hub: https://hub.docker.com/

---

Last reviewed: 2024-12-19
Next review due: 2025-01-19
