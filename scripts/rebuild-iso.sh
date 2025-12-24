#!/bin/bash
# Rebuild ISO from modified iso_root directory
# This script creates a new bootable ISO from the work/iso_root directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ISO_ROOT="$PROJECT_ROOT/work/iso_root"
OUTPUT_DIR="$PROJECT_ROOT/output"
OUTPUT_ISO="$OUTPUT_DIR/proxmox-ve-custom-firmware.iso"

# Color output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}[INFO]${NC} Rebuilding ISO from: $ISO_ROOT"
echo -e "${CYAN}[INFO]${NC} Output: $OUTPUT_ISO"

# Check requirements
if ! command -v xorriso &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} xorriso not found. Install with: sudo apt-get install xorriso"
    exit 1
fi

if [ ! -d "$ISO_ROOT" ]; then
    echo -e "${RED}[ERROR]${NC} ISO root directory not found: $ISO_ROOT"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Detect boot configuration
HAS_GRUB_BIOS=false
HAS_GRUB_EFI=false
HAS_ISOLINUX=false

if [ -f "$ISO_ROOT/boot/grub/i386-pc/eltorito.img" ]; then
    HAS_GRUB_BIOS=true
    echo -e "${CYAN}[INFO]${NC} Found GRUB BIOS boot support"
fi

if [ -f "$ISO_ROOT/efi/boot/bootx64.efi" ]; then
    HAS_GRUB_EFI=true
    echo -e "${CYAN}[INFO]${NC} Found GRUB EFI boot support"
fi

if [ -f "$ISO_ROOT/isolinux/isolinux.bin" ]; then
    HAS_ISOLINUX=true
    echo -e "${CYAN}[INFO]${NC} Found isolinux BIOS boot support"
fi

echo -e "${CYAN}[INFO]${NC} Creating ISO image..."

# Build xorriso command based on detected boot configuration
XORRISO_CMD=(
    xorriso -as mkisofs
    -o "$OUTPUT_ISO"
    -r -J -joliet-long
    -V "PROXMOX_VE"
)

# Add GRUB BIOS boot (Proxmox default)
if [ "$HAS_GRUB_BIOS" = true ]; then
    XORRISO_CMD+=(
        -b boot/grub/i386-pc/eltorito.img
        -c boot/boot.cat
        -no-emul-boot
        -boot-load-size 4
        -boot-info-table
        --grub2-boot-info
    )
    
    # Add MBR for hybrid boot if grub-pc-bin is installed
    if [ -f /usr/lib/grub/i386-pc/boot_hybrid.img ]; then
        XORRISO_CMD+=(--grub2-mbr /usr/lib/grub/i386-pc/boot_hybrid.img)
    fi
fi

# Add isolinux BIOS boot as fallback
if [ "$HAS_ISOLINUX" = true ] && [ "$HAS_GRUB_BIOS" = false ]; then
    XORRISO_CMD+=(
        -b isolinux/isolinux.bin
        -c isolinux/boot.cat
        -no-emul-boot
        -boot-load-size 4
        -boot-info-table
    )
    
    # Add MBR for hybrid boot
    if [ -f /usr/lib/ISOLINUX/isohdpfx.bin ]; then
        XORRISO_CMD+=(-isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin)
    fi
fi

# Add EFI boot support
if [ "$HAS_GRUB_EFI" = true ]; then
    # Check for EFI image
    if [ -f "$ISO_ROOT/efi.img" ]; then
        XORRISO_CMD+=(
            -eltorito-alt-boot
            -e efi.img
            -no-emul-boot
            -isohybrid-gpt-basdat
        )
    else
        # Create EFI boot from EFI directory
        XORRISO_CMD+=(
            -eltorito-alt-boot
            -e efi/boot/bootx64.efi
            -no-emul-boot
        )
    fi
fi

# Add source directory
XORRISO_CMD+=("$ISO_ROOT")

# Run xorriso
"${XORRISO_CMD[@]}" 2>&1 || {
    echo -e "${YELLOW}[WARNING]${NC} Initial xorriso command had issues, trying simplified version..."
    
    # Simplified fallback
    xorriso -as mkisofs \
        -o "$OUTPUT_ISO" \
        -r -J -joliet-long \
        -V "PROXMOX_VE" \
        -b boot/grub/i386-pc/eltorito.img \
        -c boot/boot.cat \
        -no-emul-boot \
        -boot-load-size 4 \
        -boot-info-table \
        "$ISO_ROOT" 2>&1 || {
            echo -e "${RED}[ERROR]${NC} ISO creation failed"
            exit 1
        }
}

# Show result
if [ -f "$OUTPUT_ISO" ]; then
    ISO_SIZE=$(du -h "$OUTPUT_ISO" | cut -f1)
    echo -e "${GREEN}[SUCCESS]${NC} ISO created: $OUTPUT_ISO ($ISO_SIZE)"
    echo ""
    echo -e "${CYAN}[INFO]${NC} ISO Contents Summary:"
    echo "  - Firmware files: $(find "$ISO_ROOT/firmware" -type f 2>/dev/null | wc -l)"
    echo "  - Early microcode: $(test -f "$ISO_ROOT/boot/initrd.img.orig" && echo 'Yes (combined with initrd)' || echo 'No')"
    echo "  - BIOS boot: $([ "$HAS_GRUB_BIOS" = true ] || [ "$HAS_ISOLINUX" = true ] && echo 'Yes' || echo 'No')"
    echo "  - UEFI boot: $([ "$HAS_GRUB_EFI" = true ] && echo 'Yes' || echo 'No')"
    echo "  - Post-install script: $(test -f "$ISO_ROOT/post-install-firmware.sh" && echo 'Yes' || echo 'No')"
    echo ""
    echo -e "${YELLOW}[IMPORTANT]${NC} After installation, run the post-install firmware script:"
    echo "  1. Press Ctrl+Alt+F2 to get a shell"
    echo "  2. Run: /cdrom/post-install-firmware.sh"
    echo "  3. Then reboot"
else
    echo -e "${RED}[ERROR]${NC} ISO file not created"
    exit 1
fi
