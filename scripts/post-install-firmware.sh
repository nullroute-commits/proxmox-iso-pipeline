#!/bin/bash
# Post-installation firmware setup script
# Run this from the installer shell after Proxmox installation completes
# but BEFORE rebooting to copy firmware to the installed system

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Proxmox Post-Install Firmware Setup Script            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    exit 1
fi

# Find the firmware source directory
FIRMWARE_SRC=""
for src in /cdrom/firmware /mnt/cdrom/firmware /media/cdrom/firmware; do
    if [ -d "$src" ]; then
        FIRMWARE_SRC="$src"
        break
    fi
done

if [ -z "$FIRMWARE_SRC" ]; then
    print_warning "Could not find firmware directory automatically"
    print_info "Please enter the path to the firmware directory:"
    read -r FIRMWARE_SRC
    
    if [ ! -d "$FIRMWARE_SRC" ]; then
        print_error "Directory not found: $FIRMWARE_SRC"
        exit 1
    fi
fi

print_info "Using firmware source: $FIRMWARE_SRC"

# Find the root partition of the installed system
print_info "Scanning for installed system..."

# Check for LVM (most common Proxmox setup)
if command -v vgchange &> /dev/null; then
    vgchange -ay 2>/dev/null || true
fi

# List potential root partitions
echo ""
print_info "Available partitions:"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT 2>/dev/null || fdisk -l

echo ""
print_info "Common root partition locations:"
echo "  - /dev/mapper/pve-root (LVM - most common)"
echo "  - /dev/nvme0n1p2 (NVMe)"
echo "  - /dev/sda2 (SATA)"
echo ""

# Auto-detect if possible
ROOT_DEV=""
if [ -e /dev/mapper/pve-root ]; then
    ROOT_DEV="/dev/mapper/pve-root"
    print_info "Auto-detected LVM root: $ROOT_DEV"
fi

if [ -z "$ROOT_DEV" ]; then
    print_info "Enter the root partition device (e.g., /dev/mapper/pve-root):"
    read -r ROOT_DEV
fi

if [ ! -e "$ROOT_DEV" ]; then
    print_error "Device not found: $ROOT_DEV"
    exit 1
fi

# Create mount point
MOUNT_POINT="/mnt/pve-root"
mkdir -p "$MOUNT_POINT"

# Check if already mounted
if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
    print_warning "$MOUNT_POINT is already mounted"
else
    print_info "Mounting $ROOT_DEV to $MOUNT_POINT..."
    mount "$ROOT_DEV" "$MOUNT_POINT" || {
        print_error "Failed to mount $ROOT_DEV"
        exit 1
    }
fi

# Verify it looks like a Proxmox installation
if [ ! -d "$MOUNT_POINT/etc/pve" ] && [ ! -f "$MOUNT_POINT/etc/debian_version" ]; then
    print_warning "This doesn't look like a Proxmox/Debian installation"
    print_info "Continue anyway? (y/N)"
    read -r CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        umount "$MOUNT_POINT"
        exit 1
    fi
fi

# Copy firmware
print_info "Copying firmware to installed system..."
FIRMWARE_DEST="$MOUNT_POINT/lib/firmware"
mkdir -p "$FIRMWARE_DEST"

# Count files for progress
TOTAL_FILES=$(find "$FIRMWARE_SRC" -type f | wc -l)
print_info "Copying $TOTAL_FILES firmware files..."

cp -r "$FIRMWARE_SRC"/* "$FIRMWARE_DEST"/ 2>/dev/null || {
    print_error "Failed to copy firmware"
    umount "$MOUNT_POINT"
    exit 1
}

print_success "Firmware copied successfully"

# Bind mount for chroot
print_info "Setting up chroot environment..."
mount --bind /dev "$MOUNT_POINT/dev"
mount --bind /proc "$MOUNT_POINT/proc"
mount --bind /sys "$MOUNT_POINT/sys"

# Check if /run exists and bind mount it
if [ -d "$MOUNT_POINT/run" ]; then
    mount --bind /run "$MOUNT_POINT/run"
fi

# Rebuild initramfs
print_info "Rebuilding initramfs (this may take a minute)..."
chroot "$MOUNT_POINT" update-initramfs -u -k all || {
    print_warning "Initramfs rebuild had warnings, but may still succeed"
}

print_success "Initramfs rebuilt successfully"

# Cleanup
print_info "Cleaning up..."
umount "$MOUNT_POINT/run" 2>/dev/null || true
umount "$MOUNT_POINT/sys"
umount "$MOUNT_POINT/proc"
umount "$MOUNT_POINT/dev"
umount "$MOUNT_POINT"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Firmware Setup Complete!                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
print_info "You can now safely reboot into your Proxmox installation"
print_info "Run: reboot"
echo ""
