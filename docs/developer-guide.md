# Developer Guide

> **Documentation Version:** 1.0.0  
> **Audience:** Contributors, Developers  
> **Prerequisites:** Python 3.13, Git, Docker

This guide covers setting up a development environment, code standards, testing, and contribution guidelines.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Adding Features](#adding-features)
- [Contribution Workflow](#contribution-workflow)
- [Release Process](#release-process)

## Development Environment Setup

### Prerequisites

| Tool | Version | Installation |
|------|---------|--------------|
| Python | 3.13.0 | [python.org](https://www.python.org/downloads/) |
| Git | Latest | [git-scm.com](https://git-scm.com/) |
| Docker | 20.10+ | [docker.com](https://www.docker.com/) |
| Docker Compose | V2+ | Included with Docker Desktop |

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/nullroute-commits/proxmox-iso-pipeline.git
cd proxmox-iso-pipeline

# 2. Create and activate virtual environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install in development mode with dev dependencies
pip install -e ".[dev]"

# 4. Verify installation
python -c "import src; print('Installation successful')"
```

### IDE Configuration

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Black Formatter
- Docker

`.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter"
    }
}
```

#### PyCharm

1. Set Python interpreter to `venv/bin/python`
2. Enable Black formatter: Settings → Tools → Black
3. Enable Flake8: Settings → Editor → Inspections → Python → Flake8

### Pre-commit Hooks (Optional)

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

## Code Standards

### PEP 8 Compliance

All Python code must follow [PEP 8](https://www.python.org/dev/peps/pep-0008/):

```python
# Good: Snake case for functions and variables
def download_firmware(package_name: str) -> Path:
    firmware_path = cache_dir / package_name
    return firmware_path

# Good: CamelCase for classes
class FirmwareManager:
    pass

# Good: UPPER_CASE for constants
DEFAULT_PROXMOX_VERSION = "9.1"
```

### PEP 257 Docstrings

Follow [PEP 257](https://www.python.org/dev/peps/pep-0257/) with Google-style docstrings:

```python
def download_firmware(vendor: str, force: bool = False) -> List[Path]:
    """Download firmware packages for specified vendor.

    Args:
        vendor: Hardware vendor name (nvidia, amd, intel, freeware).
        force: Force re-download even if cached.

    Returns:
        List of paths to downloaded firmware packages.

    Raises:
        FirmwareDownloadError: If download fails.

    Example:
        >>> manager = FirmwareManager(cache_dir)
        >>> packages = manager.download_firmware("nvidia")
        >>> print(len(packages))
        3
    """
    pass
```

### Type Hints

All functions must include type annotations:

```python
from pathlib import Path
from typing import List, Optional, Dict, Any

def process_config(
    config_file: Optional[Path] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> BuildConfig:
    """Process configuration from file and overrides."""
    pass
```

### Black Formatting

Code formatting is enforced with Black (88 character line length):

```bash
# Format all code
black src/

# Check formatting without changes
black --check src/

# Show diff of what would change
black --diff src/
```

### Import Order

Imports should be organized:

```python
# Standard library
import json
import logging
import os
from pathlib import Path
from typing import List, Optional

# Third-party packages
import click
import yaml
from rich.console import Console

# Local imports
from src.config import BuildConfig
from src.firmware import FirmwareManager
```

### Linting Commands

```bash
# Run all linting checks
flake8 src/
pydocstyle src/
black --check src/
mypy src/

# Or use Docker
docker compose run --rm linter
```

## Testing

### Test Structure

```
proxmox-iso-pipeline/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── test_builder.py      # Builder module tests
│   ├── test_config.py       # Config module tests
│   └── test_firmware.py     # Firmware module tests
```

### Writing Tests

Use pytest with fixtures:

```python
# tests/conftest.py
import pytest
from pathlib import Path
from src.config import BuildConfig

@pytest.fixture
def build_config(tmp_path: Path) -> BuildConfig:
    """Create a test build configuration."""
    return BuildConfig(
        proxmox_version="9.1",
        debian_release="trixie",
        output_dir=tmp_path / "output",
        work_dir=tmp_path / "work",
        firmware_cache=tmp_path / "cache",
    )

# tests/test_config.py
def test_config_defaults(build_config: BuildConfig) -> None:
    """Test default configuration values."""
    assert build_config.proxmox_version == "9.1"
    assert build_config.debian_release == "trixie"
    assert build_config.include_nvidia is True

def test_config_directory_creation(build_config: BuildConfig) -> None:
    """Test that required directories are created."""
    assert build_config.output_dir.exists()
    assert build_config.work_dir.exists()
    assert build_config.firmware_cache.exists()
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_builder.py -v

# Run specific test
pytest tests/test_config.py::test_config_defaults -v

# Run tests matching pattern
pytest tests/ -k "firmware" -v
```

### Test Coverage

Target: **80%+ code coverage**

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Adding Features

### Adding New Firmware Vendor

1. **Update firmware sources** (`config/firmware-sources.json`):

```json
{
  "new_vendor": [
    "package-name-1",
    "package-name-2"
  ]
}
```

2. **Update FirmwareManager** (if needed in `src/firmware.py`):

```python
# Add to default sources if config file doesn't exist
return {
    # ... existing vendors ...
    "new_vendor": [
        "package-name-1",
        "package-name-2",
    ],
}
```

3. **Update BuildConfig** (`src/config.py`):

```python
@dataclass
class BuildConfig:
    # ... existing fields ...
    include_new_vendor: bool = True
```

4. **Update CLI** (`src/builder.py`):

```python
@click.option(
    "--no-new-vendor",
    is_flag=True,
    help="Exclude new vendor firmware",
)
def main(
    # ... existing params ...
    no_new_vendor: bool,
) -> None:
    # ... existing code ...
    build_config.include_new_vendor = not no_new_vendor
```

5. **Add tests**:

```python
def test_new_vendor_firmware_download(firmware_manager):
    """Test downloading new vendor firmware."""
    packages = firmware_manager.download_firmware("new_vendor")
    assert len(packages) > 0
```

6. **Update documentation**:
   - `docs/user-guide.md`
   - `docs/configuration.md`
   - `README.md`

### Adding New Configuration Option

1. **Add to BuildConfig** (`src/config.py`)
2. **Add environment variable mapping** (if needed)
3. **Add CLI option** (`src/builder.py`)
4. **Add tests**
5. **Update documentation**

### Adding New Build Feature

1. **Create feature module** (if complex)
2. **Integrate with ProxmoxISOBuilder** class
3. **Add unit and integration tests**
4. **Update documentation**
5. **Add to CI/CD if needed**

## Contribution Workflow

### Branch Naming

```
feature/add-new-vendor-support
bugfix/fix-iso-extraction
docs/update-user-guide
refactor/improve-firmware-manager
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for new vendor firmware
fix: resolve ISO extraction permission error
docs: update user guide with new options
refactor: simplify firmware download logic
test: add tests for configuration module
chore: update dependencies to latest versions
```

### Pull Request Process

1. **Fork and clone** the repository
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature
   ```
3. **Make changes** following code standards
4. **Run linting and tests**:
   ```bash
   flake8 src/
   black src/
   pytest tests/ -v
   ```
5. **Commit changes** with clear messages
6. **Push and create PR**:
   ```bash
   git push origin feature/your-feature
   ```
7. **Address review feedback**

### Code Review Checklist

- [ ] Code follows PEP 8 and PEP 257
- [ ] Type hints on all functions
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] CI passes

## Release Process

### Versioning

Follow [Semantic Versioning](https://semver.org/):

- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features (backward compatible)
- **Patch** (0.0.X): Bug fixes

### Release Steps

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "1.1.0"
   ```

2. **Update VERSIONS.md** with any dependency changes

3. **Update documentation** version pins

4. **Create release commit**:
   ```bash
   git commit -am "chore: release version 1.1.0"
   ```

5. **Tag release**:
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```

6. **CI/CD automatically**:
   - Builds Docker images
   - Runs security scans
   - Generates release notes

## Next Steps

- [Architecture](architecture.md) - System design
- [API Reference](api-reference.md) - Module documentation
- [Troubleshooting](troubleshooting.md) - Common issues

---

*[Back to Documentation Index](README.md)*
