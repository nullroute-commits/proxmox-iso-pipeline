# Proxmox ISO Pipeline Documentation

> **Documentation Version:** 1.0.0  
> **Last Updated:** 2025-12-25  
> **Proxmox VE Target:** 9.1  
> **Debian Base:** Trixie (Debian 13)

Welcome to the Proxmox ISO Pipeline documentation. This multi-perspective documentation provides comprehensive guides for different audiences and use cases.

## Documentation Overview

| Document | Audience | Description |
|----------|----------|-------------|
| [User Guide](user-guide.md) | End Users | Getting started, basic usage, and common workflows |
| [Operator Guide](operator-guide.md) | DevOps/Admins | Deployment, CI/CD integration, and production setup |
| [Developer Guide](developer-guide.md) | Contributors | Development setup, code standards, and contribution guidelines |
| [Architecture](architecture.md) | Technical | System design, component overview, and data flow |
| [Configuration Reference](configuration.md) | All | Complete configuration options and environment variables |
| [Troubleshooting](troubleshooting.md) | All | Common issues, solutions, and debugging tips |
| [API Reference](api-reference.md) | Developers | Python API documentation and module reference |

## Quick Navigation

### For End Users

If you want to **build a custom Proxmox ISO** with firmware support:

1. Start with the [User Guide](user-guide.md)
2. Review [Configuration Reference](configuration.md) for customization options
3. Check [Troubleshooting](troubleshooting.md) if you encounter issues

### For DevOps/Administrators

If you want to **deploy and automate** the pipeline:

1. Read the [Operator Guide](operator-guide.md)
2. Review [Architecture](architecture.md) for system understanding
3. Configure using [Configuration Reference](configuration.md)

### For Contributors

If you want to **contribute to the project**:

1. Follow the [Developer Guide](developer-guide.md)
2. Understand the [Architecture](architecture.md)
3. Reference the [API Reference](api-reference.md) for module details

## Version Compatibility

This documentation is pinned to version **1.0.0** of the Proxmox ISO Pipeline. For version-specific details, see [VERSIONS.md](../VERSIONS.md).

| Component | Supported Version |
|-----------|------------------|
| Python | 3.13.0 |
| Proxmox VE | 9.1 |
| Debian | Trixie (13) |
| Docker | 20.10+ |
| Docker Compose | V2+ |

## Documentation Standards

All documentation in this directory follows these standards:

- **Markdown Format**: GitHub Flavored Markdown (GFM)
- **Version Pinning**: All examples use pinned versions from [VERSIONS.md](../VERSIONS.md)
- **Code Examples**: All code examples are tested and verified
- **Cross-References**: Internal links use relative paths

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/nullroute-commits/proxmox-iso-pipeline/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nullroute-commits/proxmox-iso-pipeline/discussions)
- **Main README**: [Project README](../README.md)

---

*Documentation maintained by Proxmox ISO Pipeline Contributors*
