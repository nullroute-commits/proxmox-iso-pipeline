# Multi-stage Dockerfile for Proxmox ISO builder
# Supports multiple architectures: amd64, arm64
# All package versions are pinned for reproducibility

# Stage 1: Base build environment
ARG BASE_IMAGE=debian:trixie-20241202-slim
FROM ${BASE_IMAGE} AS base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Architecture argument for conditional package installation
ARG TARGETARCH

# Install architecture-independent system dependencies with pinned versions
# These packages have the same version across all architectures
RUN apt-get update && apt-get install -y \
    python3.13=3.13.5-2 \
    python3.13-venv=3.13.5-2 \
    python3-pip=25.1.1+dfsg-1 \
    wget=1.25.0-2 \
    curl=8.14.1-2+deb13u2 \
    isolinux=3:6.04~git20190206.bf6db5b4+dfsg1-3.1 \
    sudo=1.9.16p2-3 \
    ca-certificates=20250419 \
    gnupg=2.4.7-21 \
    && rm -rf /var/lib/apt/lists/*

# Install architecture-specific packages with pinned versions
# Package versions differ between amd64 and arm64 due to binary rebuilds
RUN apt-get update && \
    if [ "$TARGETARCH" = "amd64" ]; then \
        # amd64-specific packages with pinned versions
        apt-get install -y \
            xorriso=1.5.6-1.2+b1 \
            genisoimage=9:1.1.11-4 \
            squashfs-tools=1:4.6.1-1 \
            syslinux=3:6.04~git20190206.bf6db5b4+dfsg1-3.1 \
            syslinux-utils=3:6.04~git20190206.bf6db5b4+dfsg1-3.1; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
        # arm64-specific packages with pinned versions
        # Note: syslinux is not available on arm64 (x86-only bootloader)
        # Note: squashfs-tools has arch-specific binary rebuild on arm64
        apt-get install -y \
            xorriso=1.5.6-1.2+b1 \
            genisoimage=9:1.1.11-4 \
            squashfs-tools=1:4.6.1-1+b1; \
    fi && \
    rm -rf /var/lib/apt/lists/*

# Stage 2: Python environment
FROM base AS python-env

WORKDIR /app

# Copy Python requirements
COPY pyproject.toml .flake8 ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN python3.13 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip==25.3 setuptools==78.1.1 wheel==0.45.0 && \
    /opt/venv/bin/pip install -e .

# Install development dependencies for linting
RUN /opt/venv/bin/pip install flake8==7.1.1 pydocstyle==6.3.0 black==24.10.0 mypy==1.13.0

# Stage 3: Builder stage
FROM base AS builder

WORKDIR /build

# Copy virtual environment from python-env stage
COPY --from=python-env /opt/venv /opt/venv

# Copy application code
COPY . /build/

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Create necessary directories
RUN mkdir -p /build/output /build/work /build/firmware-cache

# Stage 4: Final runtime image
FROM base AS runtime

# Build arguments for dynamic labeling
ARG IMAGE_VERSION=1.0.0
ARG PYTHON_VERSION=3.13.5
ARG PROXMOX_VERSION=9.1
ARG DEBIAN_RELEASE=trixie
ARG ARCHITECTURES=amd64,arm64
# BASE_IMAGE must be redeclared in this stage to be available for labels
ARG BASE_IMAGE

# Add OCI-compliant image labels
LABEL org.opencontainers.image.title="Proxmox ISO Pipeline Builder" \
      org.opencontainers.image.description="Custom Debian ${DEBIAN_RELEASE} based Proxmox VE ${PROXMOX_VERSION} installer builder with comprehensive firmware support for NVIDIA, AMD, and Intel hardware" \
      org.opencontainers.image.version="${IMAGE_VERSION}" \
      org.opencontainers.image.authors="Proxmox ISO Pipeline Contributors" \
      org.opencontainers.image.vendor="nullroute-commits" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.url="https://github.com/nullroute-commits/proxmox-iso-pipeline" \
      org.opencontainers.image.source="https://github.com/nullroute-commits/proxmox-iso-pipeline" \
      org.opencontainers.image.documentation="https://github.com/nullroute-commits/proxmox-iso-pipeline#readme" \
      org.opencontainers.image.base.name="${BASE_IMAGE}" \
      maintainer="Proxmox ISO Pipeline Contributors"

# Additional build metadata labels
LABEL org.proxmox_iso_pipeline.python.version="${PYTHON_VERSION}" \
      org.proxmox_iso_pipeline.debian.release="${DEBIAN_RELEASE}" \
      org.proxmox_iso_pipeline.proxmox.version="${PROXMOX_VERSION}" \
      org.proxmox_iso_pipeline.supports.architectures="${ARCHITECTURES}" \
      org.proxmox_iso_pipeline.firmware.nvidia="supported" \
      org.proxmox_iso_pipeline.firmware.amd="supported" \
      org.proxmox_iso_pipeline.firmware.intel="supported"

WORKDIR /workspace

# Copy virtual environment
COPY --from=python-env /opt/venv /opt/venv

# Copy application
COPY --from=builder /build /workspace

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user for running the application
RUN useradd -m -u 1000 builder && \
    chown -R builder:builder /workspace && \
    echo "# Allow builder to run specific commands for ISO operations" >> /etc/sudoers && \
    echo "builder ALL=(ALL) NOPASSWD: /bin/mount, /bin/umount, /bin/cp, /bin/chmod" >> /etc/sudoers

# Set default user
USER builder

# Expose volume mount points
VOLUME ["/workspace/output", "/workspace/work", "/workspace/firmware-cache"]

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["--help"]
