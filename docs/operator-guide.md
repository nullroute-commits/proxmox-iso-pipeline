# Operator Guide

> **Documentation Version:** 1.0.0  
> **Audience:** DevOps Engineers, System Administrators  
> **Prerequisites:** Docker, CI/CD, Infrastructure knowledge

This guide covers deploying, automating, and operating the Proxmox ISO Pipeline in production environments.

## Table of Contents

- [Deployment Options](#deployment-options)
- [CI/CD Integration](#cicd-integration)
- [Production Configuration](#production-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Security Considerations](#security-considerations)
- [Scaling and Performance](#scaling-and-performance)
- [Maintenance Procedures](#maintenance-procedures)

## Deployment Options

### Option 1: Docker Compose (Single Host)

Best for: Small teams, single-server deployments

```bash
# Clone and deploy
git clone https://github.com/nullroute-commits/proxmox-iso-pipeline.git
cd proxmox-iso-pipeline

# Build and run
docker compose up -d builder
```

### Option 2: GitHub Actions (Automated)

Best for: Continuous integration, automated builds

The included workflow (`.github/workflows/build-iso.yml`) provides:
- Automated linting and testing
- Multi-architecture Docker builds
- Security scanning with Trivy
- Release automation

### Option 3: Container Registry Deployment

Best for: Air-gapped environments, standardized deployments

```bash
# Pull pre-built image (when using GitHub Container Registry)
docker pull ghcr.io/nullroute-commits/proxmox-iso-pipeline:main

# Run directly
docker run --rm --privileged \
  -v $(pwd)/output:/workspace/output \
  -v $(pwd)/work:/workspace/work \
  -v $(pwd)/firmware-cache:/workspace/firmware-cache \
  ghcr.io/nullroute-commits/proxmox-iso-pipeline:main build
```

### Option 4: Standalone Operation (Without GitHub)

Best for: Air-gapped environments, fully offline operation

The pipeline can operate completely without GitHub access:

```bash
# Clone or copy the repository to your target system
cd proxmox-iso-pipeline

# Build Docker image locally (no remote registry access needed)
docker compose build

# Run the builder
docker compose run --rm builder build
```

**Notes for offline operation:**
- The Docker image is built locally from the Dockerfile
- No connection to `ghcr.io` or GitHub is required
- Firmware packages are downloaded from Debian mirrors (requires internet or local mirror)
- You can pre-populate the `firmware-cache/` directory for fully offline builds

## CI/CD Integration

### GitHub Actions

The repository includes a complete CI/CD pipeline:

```yaml
# .github/workflows/build-iso.yml (excerpt)
name: Build Proxmox ISO

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      proxmox_version:
        description: 'Proxmox VE version'
        default: '9.1'
```

#### Triggering Builds

**Automatic Triggers:**
- Push to `main` or `develop` branches
- Pull request to `main`

**Manual Trigger:**
1. Navigate to Actions tab
2. Select "Build Proxmox ISO"
3. Click "Run workflow"
4. Configure options and run

#### Workflow Jobs

| Job | Purpose | Duration |
|-----|---------|----------|
| `lint` | Code quality checks | ~2 min |
| `build-docker` | Multi-arch image build | ~10 min |
| `test` | Pytest execution | ~3 min |
| `security-scan` | Trivy vulnerability scan | ~5 min |
| `release` | Release notes generation | ~1 min |

### GitLab CI Integration

Example `.gitlab-ci.yml`:

```yaml
stages:
  - lint
  - build
  - test
  - deploy

variables:
  PROXMOX_VERSION: "9.1"
  DEBIAN_RELEASE: "trixie"

lint:
  stage: lint
  image: python:3.13.0-slim
  script:
    - pip install flake8==7.1.1 pydocstyle==6.3.0 black==24.10.0
    - flake8 src/
    - pydocstyle src/
    - black --check src/

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker compose build
    - docker compose run --rm builder build
  artifacts:
    paths:
      - output/*.iso
    expire_in: 1 week
```

### Jenkins Integration

Example `Jenkinsfile`:

```groovy
pipeline {
    agent {
        docker {
            image 'docker:24-dind'
            args '--privileged'
        }
    }
    
    environment {
        PROXMOX_VERSION = '9.1'
        DEBIAN_RELEASE = 'trixie'
    }
    
    stages {
        stage('Build Image') {
            steps {
                sh 'docker compose build'
            }
        }
        
        stage('Lint') {
            steps {
                sh 'docker compose run --rm linter'
            }
        }
        
        stage('Build ISO') {
            steps {
                sh 'docker compose run --rm builder build'
            }
        }
    }
    
    post {
        success {
            archiveArtifacts artifacts: 'output/*.iso'
        }
    }
}
```

## Production Configuration

### Environment Variables

```bash
# Core Configuration
PROXMOX_VERSION=9.1
DEBIAN_RELEASE=trixie

# Firmware Options
INCLUDE_NVIDIA=true
INCLUDE_AMD=true
INCLUDE_INTEL=true

# Build Configuration
BUILD_ARCH=linux/amd64,linux/arm64

# Directory Paths (for volume mounting)
OUTPUT_DIR=/data/iso-output
WORK_DIR=/data/iso-work
FIRMWARE_CACHE=/data/firmware-cache
```

### Docker Compose Production Override

Create `docker-compose.prod.yml`:

```yaml
version: '3.9'

services:
  builder:
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "100m"
        max-file: "3"
    volumes:
      - /data/output:/workspace/output
      - /data/work:/workspace/work
      - /data/firmware-cache:/workspace/firmware-cache
      - /data/config:/workspace/config:ro
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

Run with production config:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Resource Requirements

| Resource | Minimum | Recommended | High Performance |
|----------|---------|-------------|------------------|
| CPU Cores | 2 | 4 | 8+ |
| RAM | 4GB | 8GB | 16GB+ |
| Disk Space | 20GB | 50GB | 100GB+ |
| Disk Type | HDD | SSD | NVMe |

### Network Configuration

The builder requires outbound internet access for:

| Domain | Purpose | Port | Required |
|--------|---------|------|----------|
| `enterprise.proxmox.com` | ISO download | 443 | Yes |
| `deb.debian.org` | Firmware packages | 80 | Yes |
| `ghcr.io` | Pre-built container images (optional) | 443 | No |

**Note:** The pipeline works without `ghcr.io` access when building Docker images locally.

Firewall rules example (iptables):

```bash
# Allow outbound HTTPS
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

# Allow outbound HTTP (Debian mirrors)
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
```

## Monitoring and Logging

### Docker Logs

```bash
# View builder logs
docker compose logs -f builder

# View last 100 lines
docker compose logs --tail=100 builder

# Export logs to file
docker compose logs builder > builder.log 2>&1
```

### Build Metrics

Track build performance:

```bash
# Time the build process
time docker compose run --rm builder build

# Monitor resource usage during build
docker stats proxmox-iso-builder
```

### Health Checks

Add to `docker-compose.yml`:

```yaml
services:
  builder:
    healthcheck:
      test: ["CMD", "python", "-c", "import src; print('OK')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### Alerting Integration

Example Prometheus metrics endpoint (add to builder):

```python
# Example: Add to src/builder.py for metrics
from prometheus_client import Counter, Histogram

BUILD_COUNTER = Counter('iso_builds_total', 'Total ISO builds')
BUILD_DURATION = Histogram('iso_build_duration_seconds', 'ISO build duration')
```

## Security Considerations

### Image Security

1. **Pinned Versions**: All dependencies are pinned (see [VERSIONS.md](../VERSIONS.md))
2. **Vulnerability Scanning**: Trivy scans in CI/CD pipeline
3. **Non-root User**: Builder runs as non-root user `builder`

### Secrets Management

Never commit secrets. Use environment variables or secret managers:

```bash
# Using Docker secrets
echo "my-registry-token" | docker secret create registry_token -

# In docker-compose.yml
services:
  builder:
    secrets:
      - registry_token
    environment:
      - REGISTRY_TOKEN_FILE=/run/secrets/registry_token

secrets:
  registry_token:
    external: true
```

### Network Security

- Build in isolated network segments
- Use network policies if in Kubernetes
- Consider air-gapped builds for sensitive environments

### Privileged Mode

The builder requires `--privileged` for ISO mounting. Mitigate risks:

```yaml
# More restrictive capability set
services:
  builder:
    cap_add:
      - SYS_ADMIN
      - MKNOD
    cap_drop:
      - ALL
    security_opt:
      - apparmor:docker-default
```

## Scaling and Performance

### Parallel Builds

Run multiple architecture builds in parallel:

```bash
# Build amd64 and arm64 simultaneously
docker buildx build --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile -t proxmox-iso-builder:latest .
```

### Caching Strategies

**Firmware Cache:**
```yaml
volumes:
  firmware-cache:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/shared-firmware-cache
```

**Docker Layer Cache:**

For local builds (default, no GitHub required):
```yaml
services:
  builder:
    build:
      cache_from:
        - type=local,src=/tmp/.buildx-cache
```

For builds with GitHub Container Registry access:
```yaml
services:
  builder:
    build:
      cache_from:
        - type=registry,ref=ghcr.io/nullroute-commits/proxmox-iso-builder:cache
```

### Build Optimization

| Optimization | Impact | Implementation |
|--------------|--------|----------------|
| SSD Storage | 2-3x faster | Mount work dirs on SSD |
| Firmware Cache | Skip downloads | Persist firmware-cache volume |
| Docker Cache | Faster rebuilds | Use BuildKit cache |
| More CPU | Linear improvement | Allocate more cores |

## Maintenance Procedures

### Updating Dependencies

1. Review [VERSIONS.md](../VERSIONS.md) for current versions
2. Check for security advisories
3. Test updates in staging environment
4. Update pinned versions
5. Run full test suite

```bash
# Check for outdated packages
pip list --outdated

# Update a specific package
pip install --upgrade package-name==new.version
```

### Clearing Caches

```bash
# Clear work directory
rm -rf work/*

# Clear firmware cache
rm -rf firmware-cache/*

# Clear Docker build cache
docker builder prune

# Full cleanup
docker compose down -v
docker system prune -af
```

### Backup Procedures

```bash
# Backup firmware cache (for air-gapped deployments)
tar -czvf firmware-cache-backup.tar.gz firmware-cache/

# Backup configuration
tar -czvf config-backup.tar.gz config/

# Backup output ISOs
rsync -avz output/ /backup/iso-archive/
```

### Disaster Recovery

1. **Builder Failure**: Rebuild Docker image from source
2. **Corrupted Cache**: Clear and re-download
3. **Version Mismatch**: Refer to [VERSIONS.md](../VERSIONS.md) for exact versions

## Next Steps

- [Architecture](architecture.md) - System design details
- [Configuration Reference](configuration.md) - All options
- [Troubleshooting](troubleshooting.md) - Issue resolution

---

*[Back to Documentation Index](README.md)*
