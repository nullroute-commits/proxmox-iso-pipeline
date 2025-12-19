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
| requests | 2.32.4 | HTTP library for downloading files |
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
| pip | 25.3 | Package installer |
| setuptools | 78.1.1 | Package builder |
| wheel | 0.45.0 | Wheel package support |

## System Packages (Debian Trixie)

### Base Image
- **debian**: trixie-20241202-slim

### System Dependencies
All versions are pinned for reproducibility. Some packages have architecture-specific versions.

#### Architecture-Independent Packages
| Package | Version | Purpose |
|---------|---------|---------|
| python3.13 | 3.13.5-2 | Python runtime |
| python3.13-venv | 3.13.5-2 | Virtual environment support |
| python3-pip | 25.1.1+dfsg-1 | Python package installer |
| wget | 1.25.0-2 | File downloader |
| curl | 8.14.1-2+deb13u2 | Transfer tool |
| isolinux | 3:6.04~git20190206.bf6db5b4+dfsg1-3.1 | Boot loader (arch: all) |
| squashfs-tools | 1:4.6.1-1 | SquashFS filesystem tools |
| sudo | 1.9.16p2-3 | Privilege escalation |
| ca-certificates | 20250419 | SSL certificates |
| gnupg | 2.4.7-21 | GPG encryption |

#### Architecture-Specific Packages (amd64)
| Package | Version | Purpose |
|---------|---------|---------|
| xorriso | 1.5.6-1.2+b1 | ISO image creator |
| genisoimage | 9:1.1.11-4 | ISO creation tool |
| syslinux | 3:6.04~git20190206.bf6db5b4+dfsg1-3.1 | Boot loader suite (legacy BIOS) |
| syslinux-utils | 3:6.04~git20190206.bf6db5b4+dfsg1-3.1 | Syslinux utilities |

#### Architecture-Specific Packages (arm64)
| Package | Version | Purpose |
|---------|---------|---------|
| xorriso | 1.5.6-1.2+b1 | ISO image creator |
| genisoimage | 9:1.1.11-4 | ISO creation tool |

**Note**: `syslinux` and `syslinux-utils` are x86-specific packages required for legacy BIOS boot support.
They are not available on ARM64 architecture and are only installed on amd64 builds.

## GitHub Actions

### Actions
All actions are pinned to commit hashes for security (preventing supply chain attacks).

| Action | Version | Commit Hash | Purpose |
|--------|---------|-------------|---------|
| actions/checkout | v6.0.1 | 8e8c483db84b4bee98b60c0593521ed34d9990e8 | Repository checkout |
| actions/setup-python | v6.1.0 | 83679a892e2d95755f2dac6acb0bfd1e9ac5d548 | Python environment setup |
| docker/setup-qemu-action | v3.7.0 | c7c53464625b32c7a7e944ae62b3e17d2b600130 | QEMU emulation for multi-arch |
| docker/setup-buildx-action | v3.12.0 | 8d2750c68a42422c14e847fe6c8ac0403b4cbd6f | Docker Buildx setup |
| docker/login-action | v3.6.0 | 5e57cd118135c172c3672efd75eb46360885c0ef | Docker registry login |
| docker/metadata-action | v5.10.0 | c299e40c65443455700f0fdfc63efafe5b349051 | Docker metadata extraction |
| docker/build-push-action | v6.18.0 | 263435318d21b8e681c14492fe198d362a7d2c83 | Docker image build/push |
| aquasecurity/trivy-action | 0.33.1 | b6643a29fecd7f34b3597bc6acb0a98b03d33ff8 | Security vulnerability scanning |
| github/codeql-action/upload-sarif | v4.31.9 | 7c9a7896f03bb1f3de14c5663ed46759e27443e0 | CodeQL SARIF upload |

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

- All versions are pinned to prevent supply chain attacks
- Architecture-specific packages use divergent process flows with pinned versions
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
