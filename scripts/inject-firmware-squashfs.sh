#!/bin/bash
# Inject firmware into pve-base.squashfs for the installed system
# This ensures firmware is available in the installed Proxmox system at first boot

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ISO_ROOT="${1:-$PROJECT_ROOT/work/iso_root}"
FIRMWARE_DIR="$ISO_ROOT/firmware"
SQUASHFS_PATH="$ISO_ROOT/pve-base.squashfs"
WORK_DIR="$PROJECT_ROOT/work/squashfs_work"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

# Check for required tools
for tool in unsquashfs mksquashfs; do
    if ! command -v $tool &> /dev/null; then
        print_error "$tool not found. Install with: apt-get install squashfs-tools"
        exit 1
    fi
done

# Check for squashfs
if [ ! -f "$SQUASHFS_PATH" ]; then
    print_error "pve-base.squashfs not found at: $SQUASHFS_PATH"
    exit 1
fi

# Check for firmware directory
if [ ! -d "$FIRMWARE_DIR" ]; then
    print_error "Firmware directory not found at: $FIRMWARE_DIR"
    print_info "Run the firmware download/injection steps first"
    exit 1
fi

FIRMWARE_COUNT=$(find "$FIRMWARE_DIR" -type f | wc -l)
if [ "$FIRMWARE_COUNT" -eq 0 ]; then
    print_warning "No firmware files found in $FIRMWARE_DIR"
    exit 0
fi

print_info "Injecting firmware into pve-base.squashfs..."
print_info "This ensures firmware is available in the installed system"
print_info "Squashfs: $SQUASHFS_PATH"
print_info "Firmware source: $FIRMWARE_DIR ($FIRMWARE_COUNT files)"
echo ""

# Clean up any previous work
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

EXTRACT_DIR="$WORK_DIR/pve-base"

# Extract squashfs
print_info "Extracting pve-base.squashfs (this may take a minute)..."
unsquashfs -d "$EXTRACT_DIR" "$SQUASHFS_PATH" || {
    print_error "Failed to extract squashfs"
    rm -rf "$WORK_DIR"
    exit 1
}

# Copy firmware
print_info "Copying firmware to extracted filesystem..."
DEST_FIRMWARE="$EXTRACT_DIR/lib/firmware"
mkdir -p "$DEST_FIRMWARE"

cp -r "$FIRMWARE_DIR"/* "$DEST_FIRMWARE"/ || {
    print_error "Failed to copy firmware"
    rm -rf "$WORK_DIR"
    exit 1
}

COPIED_COUNT=$(find "$DEST_FIRMWARE" -type f | wc -l)
print_success "Copied $COPIED_COUNT firmware files"

# Backup original squashfs
print_info "Backing up original squashfs..."
mv "$SQUASHFS_PATH" "${SQUASHFS_PATH}.orig"

# Get original size for comparison
ORIG_SIZE=$(stat -c%s "${SQUASHFS_PATH}.orig")

# Repack squashfs
print_info "Repacking squashfs (this may take several minutes)..."
print_info "Using XZ compression with x86 BCJ filter for best compression..."

mksquashfs "$EXTRACT_DIR" "$SQUASHFS_PATH" \
    -comp xz \
    -Xbcj x86 \
    -b 1M \
    -no-progress \
    2>&1 || {
    print_error "Failed to repack squashfs"
    print_info "Restoring original squashfs..."
    mv "${SQUASHFS_PATH}.orig" "$SQUASHFS_PATH"
    rm -rf "$WORK_DIR"
    exit 1
}

# Report sizes
NEW_SIZE=$(stat -c%s "$SQUASHFS_PATH")
SIZE_DIFF=$((NEW_SIZE - ORIG_SIZE))
SIZE_DIFF_MB=$((SIZE_DIFF / 1024 / 1024))
ORIG_SIZE_MB=$((ORIG_SIZE / 1024 / 1024))
NEW_SIZE_MB=$((NEW_SIZE / 1024 / 1024))

echo ""
print_success "Squashfs repacked successfully!"
print_info "Original size: ${ORIG_SIZE_MB}MB"
print_info "New size: ${NEW_SIZE_MB}MB (+${SIZE_DIFF_MB}MB for firmware)"
echo ""

# Clean up extraction directory
print_info "Cleaning up..."
rm -rf "$EXTRACT_DIR"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Firmware Injection Complete!                           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
print_info "The installed system will now have all firmware available at first boot"
print_info "No manual post-install steps required!"
echo ""
