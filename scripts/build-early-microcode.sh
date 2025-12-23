#!/bin/bash
# Build early microcode initramfs for Intel/AMD CPUs
# This creates an early cpio archive that gets loaded before the main initrd

set -e

ISO_ROOT="${1:-./work/iso_root}"
FIRMWARE_DIR="$ISO_ROOT/firmware"

# Color output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${CYAN}[INFO]${NC} Building early microcode initramfs..."

# Check for microcode directories
INTEL_UCODE="$FIRMWARE_DIR/intel-ucode"
AMD_UCODE="$FIRMWARE_DIR/amd-ucode"

if [ ! -d "$INTEL_UCODE" ] && [ ! -d "$AMD_UCODE" ]; then
    echo -e "${YELLOW}[WARNING]${NC} No microcode found in $FIRMWARE_DIR"
    exit 0
fi

# Create temporary directory for building cpio
WORK_DIR=$(mktemp -d)
mkdir -p "$WORK_DIR/kernel/x86/microcode"

MICROCODE_ADDED=false

# Add Intel microcode
if [ -d "$INTEL_UCODE" ] && [ "$(ls -A "$INTEL_UCODE" 2>/dev/null)" ]; then
    echo -e "${CYAN}[INFO]${NC} Adding Intel microcode..."
    cat "$INTEL_UCODE"/* > "$WORK_DIR/kernel/x86/microcode/GenuineIntel.bin" 2>/dev/null || true
    if [ -s "$WORK_DIR/kernel/x86/microcode/GenuineIntel.bin" ]; then
        INTEL_SIZE=$(stat -c%s "$WORK_DIR/kernel/x86/microcode/GenuineIntel.bin")
        echo -e "${GREEN}[SUCCESS]${NC} Intel microcode: ${INTEL_SIZE} bytes"
        MICROCODE_ADDED=true
    fi
fi

# Add AMD microcode
if [ -d "$AMD_UCODE" ] && [ "$(ls -A "$AMD_UCODE" 2>/dev/null)" ]; then
    echo -e "${CYAN}[INFO]${NC} Adding AMD microcode..."
    cat "$AMD_UCODE"/* > "$WORK_DIR/kernel/x86/microcode/AuthenticAMD.bin" 2>/dev/null || true
    if [ -s "$WORK_DIR/kernel/x86/microcode/AuthenticAMD.bin" ]; then
        AMD_SIZE=$(stat -c%s "$WORK_DIR/kernel/x86/microcode/AuthenticAMD.bin")
        echo -e "${GREEN}[SUCCESS]${NC} AMD microcode: ${AMD_SIZE} bytes"
        MICROCODE_ADDED=true
    fi
fi

if [ "$MICROCODE_ADDED" = false ]; then
    echo -e "${YELLOW}[WARNING]${NC} No microcode was added"
    rm -rf "$WORK_DIR"
    exit 0
fi

# Create early cpio archive (uncompressed, as required for early microcode)
EARLY_CPIO="$ISO_ROOT/boot/early_ucode.cpio"
cd "$WORK_DIR"
find . | cpio -o -H newc > "$EARLY_CPIO" 2>/dev/null
CPIO_SIZE=$(stat -c%s "$EARLY_CPIO")
echo -e "${GREEN}[SUCCESS]${NC} Created early microcode cpio: ${CPIO_SIZE} bytes"

# Backup original initrd
INITRD="$ISO_ROOT/boot/initrd.img"
if [ -f "$INITRD" ]; then
    echo -e "${CYAN}[INFO]${NC} Prepending microcode to initrd..."
    
    # Create new combined initrd: early_ucode + original initrd
    COMBINED_INITRD="$ISO_ROOT/boot/initrd.img.new"
    cat "$EARLY_CPIO" "$INITRD" > "$COMBINED_INITRD"
    
    # Backup and replace
    mv "$INITRD" "$INITRD.orig"
    mv "$COMBINED_INITRD" "$INITRD"
    
    NEW_SIZE=$(stat -c%s "$INITRD")
    ORIG_SIZE=$(stat -c%s "$INITRD.orig")
    echo -e "${GREEN}[SUCCESS]${NC} Combined initrd: ${NEW_SIZE} bytes (was ${ORIG_SIZE})"
fi

# Cleanup
rm -f "$EARLY_CPIO"
rm -rf "$WORK_DIR"

echo -e "${GREEN}[SUCCESS]${NC} Early microcode loading configured!"
