#!/bin/bash
# Entrypoint script for Proxmox ISO builder container

set -e

# Function to print colored output
print_info() {
    echo -e "\033[0;36m[INFO]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

# Display banner
cat << 'EOF'
╔═══════════════════════════════════════════════════════╗
║     Proxmox ISO Pipeline Builder                     ║
║     Multi-arch Custom Installer Builder              ║
╚═══════════════════════════════════════════════════════╝
EOF

print_info "Container started"
print_info "Python version: $(python --version)"
print_info "Architecture: $(uname -m)"

# Check if running as root (needed for ISO operations)
if [ "$EUID" -eq 0 ]; then
    print_info "Running with elevated privileges (required for ISO operations)"
fi

# Ensure output directories exist
mkdir -p /workspace/output /workspace/work /workspace/firmware-cache

# Run the main application
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    print_info "Running Proxmox ISO builder help..."
    exec python -m src.builder --help
elif [ "$1" = "lint" ]; then
    print_info "Running code linting..."
    print_info "Checking PEP8 compliance with flake8..."
    flake8 src/
    print_success "PEP8 check passed!"
    
    print_info "Checking PEP257 compliance with pydocstyle..."
    pydocstyle src/
    print_success "PEP257 check passed!"
    
    print_info "Running Black formatter check..."
    black --check src/
    print_success "Black formatting check passed!"
elif [ "$1" = "build" ]; then
    shift
    print_info "Starting ISO build process..."
    exec python -m src.builder "$@"
else
    # Pass through any other commands
    exec "$@"
fi
