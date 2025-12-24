# Security Policy

## Supported Versions

The following versions of the Proxmox ISO Pipeline are currently supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do not** create a public GitHub issue for security vulnerabilities
2. **Email** the security concern to the repository maintainers via GitHub's private vulnerability reporting feature
3. Include a detailed description of the vulnerability and steps to reproduce it
4. You can expect an initial response within 48 hours
5. We will work with you to understand and resolve the issue

### What to Expect

- **Accepted vulnerabilities**: We will work on a fix and coordinate disclosure timing with you
- **Declined reports**: We will explain why the report was not accepted as a security vulnerability

## Security Practices

This project follows security best practices:

- All dependencies are pinned to specific versions (see [VERSIONS.md](VERSIONS.md))
- GitHub Actions are pinned to commit hashes to prevent supply chain attacks
- Container images use non-root users where possible
- Regular security scans with Trivy in CI/CD pipeline
- Code quality checks with static analysis tools
