# Multi-stage Dockerfile for Proxmox ISO builder
# Supports multiple architectures: amd64, arm64

# Stage 1: Base build environment
FROM debian:trixie-20241202-slim AS base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies from Debian Trixie repository
# Note: Version pins removed as they don't exist in Trixie
# Latest available versions will be installed
RUN apt-get update && apt-get install -y \
    python3.13 \
    python3.13-venv \
    python3-pip \
    wget \
    curl \
    xorriso \
    isolinux \
    syslinux \
    syslinux-utils \
    genisoimage \
    squashfs-tools \
    sudo \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Python environment
FROM base AS python-env

WORKDIR /app

# Copy Python requirements
COPY pyproject.toml .flake8 ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN python3.13 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip==24.3.1 setuptools==75.6.0 wheel==0.45.0 && \
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
    chown -R builder:builder /workspace

# Set default user
USER builder

# Expose volume mount points
VOLUME ["/workspace/output", "/workspace/work", "/workspace/firmware-cache"]

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["--help"]
