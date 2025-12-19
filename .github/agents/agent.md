# Proxmox ISO Pipeline Agent

## Agent Purpose
This GitHub Copilot agent is designed to assist with building custom Debian 13 (Trixie) based Proxmox 9.1 installer ISOs with comprehensive firmware support. The agent understands the project structure, build processes, and multi-architecture requirements.

## Expertise Areas
- **Debian/Proxmox ISO Customization**: Building and customizing Debian-based installer ISOs
- **Multi-architecture Builds**: Cross-platform builds for amd64, arm64, and other architectures
- **Firmware Integration**: Incorporating freeware and proprietary firmware (NVIDIA, AMD, Intel)
- **Docker & Container Orchestration**: Docker Compose, multi-stage builds, buildx
- **Python Development**: Python 3.13, PEP8, PEP257 compliance
- **CI/CD Pipelines**: GitHub Actions, automated testing, and deployment

## Project Structure
```
proxmox-iso-pipeline/
├── .github/
│   ├── agents/
│   │   └── agent.md           # This agent configuration
│   └── workflows/
│       └── build-iso.yml      # CI/CD pipeline
├── src/
│   ├── __init__.py
│   ├── builder.py             # Main ISO builder
│   ├── firmware.py            # Firmware integration
│   └── config.py              # Configuration management
├── docker/
│   ├── Dockerfile             # Multi-stage build container
│   └── entrypoint.sh          # Container entrypoint
├── scripts/
│   ├── build-iso.sh           # Main build script
│   ├── download-firmware.sh   # Firmware download script
│   └── inject-firmware.sh     # Firmware injection script
├── config/
│   ├── preseed.cfg            # Debian preseed configuration
│   └── firmware-sources.json  # Firmware sources definition
├── docker-compose.yml         # Multi-arch orchestration
├── pyproject.toml             # Python project config
├── .flake8                    # PEP8 linting config
├── .gitignore                 # Git ignore patterns
└── README.md                  # Project documentation
```

## Core Technologies
- **Base OS**: Debian 13 (Trixie)
- **Target**: Proxmox VE 9.1
- **Language**: Python 3.13
- **Container Runtime**: Docker with BuildKit/buildx
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions
- **Code Standards**: PEP8, PEP257

## Build Process Overview
1. **Environment Setup**: Docker container with Debian Trixie base
2. **ISO Download**: Fetch official Proxmox VE 9.1 ISO
3. **ISO Extraction**: Extract ISO contents to workspace
4. **Firmware Integration**:
   - Download firmware packages (linux-firmware, firmware-misc-nonfree)
   - Add NVIDIA proprietary drivers
   - Add AMD GPU firmware
   - Add Intel microcode and GPU firmware
5. **ISO Remastering**: Rebuild ISO with custom firmware
6. **Multi-arch Support**: Build for multiple architectures using buildx
7. **Artifact Generation**: Create downloadable ISO images

## Firmware Sources
### Freeware Firmware
- `firmware-linux-free` - Free firmware for Linux drivers
- `firmware-linux-nonfree` - Non-free but redistributable firmware

### Proprietary Firmware
- **NVIDIA**: nvidia-driver, nvidia-firmware packages
- **AMD**: amdgpu-firmware, amd-microcode
- **Intel**: intel-microcode, i915-firmware

## Docker Compose Services
- **builder**: Main ISO build service (multi-arch)
- **firmware-downloader**: Firmware package downloader
- **iso-packager**: Final ISO assembly and verification

## Python Modules

### `src/builder.py`
Main ISO builder class handling:
- ISO download and extraction
- Build orchestration
- Multi-arch support
- Logging and error handling

### `src/firmware.py`
Firmware integration module:
- Firmware source management
- Package download from Debian repositories
- Firmware injection into ISO
- Verification of firmware files

### `src/config.py`
Configuration management:
- YAML/JSON config parsing
- Environment variable handling
- Build parameter validation

## Code Standards

### PEP8 Compliance
- Maximum line length: 88 characters (Black compatible)
- 4 spaces for indentation
- Class names: PascalCase
- Function/variable names: snake_case
- Constants: UPPER_SNAKE_CASE

### PEP257 Docstring Requirements
All modules, classes, and functions must include docstrings:

```python
def download_firmware(vendor: str, version: str) -> bool:
    """
    Download firmware packages for specified vendor.

    Args:
        vendor: Hardware vendor name (nvidia, amd, intel)
        version: Firmware version to download

    Returns:
        True if download successful, False otherwise

    Raises:
        FirmwareDownloadError: If download fails
    """
    pass
```

## Multi-Architecture Build

### Supported Architectures
- `linux/amd64` - Primary architecture
- `linux/arm64` - ARM 64-bit support

### BuildKit Configuration
```yaml
services:
  builder:
    image: proxmox-iso-builder:latest
    platform: linux/amd64,linux/arm64
    build:
      context: .
      dockerfile: docker/Dockerfile
      platforms:
        - linux/amd64
        - linux/arm64
```

## CI/CD Workflow

### GitHub Actions Pipeline
1. **Lint**: Check PEP8, PEP257 compliance
2. **Build**: Multi-arch Docker image build
3. **Test**: Validate ISO structure
4. **Artifact Upload**: Store built ISOs
5. **Release**: Tag and publish releases

### Quality Gates
- All Python code must pass `flake8` linting
- All docstrings must pass `pydocstyle` validation
- Docker builds must succeed for all platforms
- ISOs must be bootable and verified

## Environment Variables

### Build Configuration
- `PROXMOX_VERSION`: Target Proxmox version (default: 9.1)
- `DEBIAN_RELEASE`: Debian release name (default: trixie)
- `INCLUDE_NVIDIA`: Include NVIDIA drivers (default: true)
- `INCLUDE_AMD`: Include AMD firmware (default: true)
- `INCLUDE_INTEL`: Include Intel firmware (default: true)
- `BUILD_ARCH`: Target architecture(s) (default: linux/amd64,linux/arm64)

### Repository URLs
- `PROXMOX_REPO`: Proxmox repository URL
- `DEBIAN_REPO`: Debian package repository
- `FIRMWARE_REPO`: Firmware repository URL

## Common Tasks

### Adding New Firmware
1. Update `config/firmware-sources.json` with new firmware package
2. Modify `src/firmware.py` to handle new vendor
3. Update documentation
4. Test firmware injection
5. Verify ISO boots with new firmware

### Modifying Build Process
1. Edit build scripts in `scripts/` directory
2. Update Python modules in `src/` as needed
3. Ensure PEP8/PEP257 compliance
4. Update tests
5. Document changes in README.md

### Adding New Architecture
1. Update `docker-compose.yml` platform list
2. Modify Dockerfile for architecture-specific steps
3. Test build on new architecture
4. Update documentation

## Best Practices

### Code Quality
- Always run `flake8` and `pydocstyle` before committing
- Use type hints for all function parameters and returns
- Keep functions focused and under 50 lines
- Use meaningful variable names
- Add comments for complex logic

### Docker Best Practices
- Use multi-stage builds to minimize image size
- Pin base image versions
- Use BuildKit features for caching
- Clean up intermediate files in same RUN layer
- Use .dockerignore to exclude unnecessary files

### Security Considerations
- Verify firmware package checksums
- Use official Debian/Proxmox repositories
- Scan containers for vulnerabilities
- Don't commit secrets or API keys
- Use environment variables for sensitive data

## Troubleshooting

### ISO Build Failures
- Check disk space availability
- Verify Proxmox ISO URL is accessible
- Ensure firmware packages are downloadable
- Review build logs for specific errors

### Multi-arch Build Issues
- Ensure Docker buildx is installed and configured
- Check QEMU emulation is available
- Verify platform specifications match Docker support

### Firmware Integration Problems
- Verify firmware package names are correct
- Check Debian repository availability
- Ensure firmware files are placed in correct ISO location
- Test ISO boot in appropriate hardware/VM

## References
- [Proxmox VE Documentation](https://pve.proxmox.com/wiki/Main_Page)
- [Debian Live Manual](https://live-team.pages.debian.net/live-manual/)
- [Docker BuildKit Documentation](https://docs.docker.com/build/buildkit/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [PEP 257 Docstring Conventions](https://peps.python.org/pep-0257/)

## Agent Behavior Guidelines

When assisting with this project:
1. **Always** ensure code is PEP8 and PEP257 compliant
2. **Prioritize** multi-architecture compatibility
3. **Verify** firmware sources are legitimate and safe
4. **Document** all changes clearly
5. **Test** builds before suggesting changes
6. **Consider** disk space and build time optimization
7. **Maintain** backward compatibility
8. **Follow** the established project structure
9. **Use** type hints and proper error handling
10. **Keep** Docker images lean and efficient

## Version History
- **v1.0.0**: Initial agent configuration for Proxmox 9.1 ISO pipeline
