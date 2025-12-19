#!/bin/bash
# Firmware injection script

set -e

ISO_ROOT="${1:-./work/iso_root}"
FIRMWARE_DIR="${2:-./firmware-cache}"

if [ ! -d "$ISO_ROOT" ]; then
    echo "[ERROR] ISO root directory not found: $ISO_ROOT"
    exit 1
fi

if [ ! -d "$FIRMWARE_DIR" ]; then
    echo "[ERROR] Firmware directory not found: $FIRMWARE_DIR"
    exit 1
fi

echo "[INFO] Injecting firmware into ISO..."
echo "[INFO] ISO Root: $ISO_ROOT"
echo "[INFO] Firmware Source: $FIRMWARE_DIR"

# Create firmware directory in ISO
DEST_DIR="$ISO_ROOT/firmware"
mkdir -p "$DEST_DIR"

# Extract and copy firmware from .deb packages
for deb_file in "$FIRMWARE_DIR"/*.deb; do
    if [ -f "$deb_file" ]; then
        echo "[INFO] Processing: $(basename "$deb_file")"
        
        # Create temporary extraction directory
        TEMP_DIR=$(mktemp -d)
        
        # Extract .deb package
        dpkg-deb -x "$deb_file" "$TEMP_DIR" 2>/dev/null || {
            echo "[WARNING] Failed to extract: $(basename "$deb_file")"
            rm -rf "$TEMP_DIR"
            continue
        }
        
        # Copy firmware files if they exist
        if [ -d "$TEMP_DIR/lib/firmware" ]; then
            cp -r "$TEMP_DIR/lib/firmware/"* "$DEST_DIR/" 2>/dev/null || true
            echo "[SUCCESS] Copied firmware from: $(basename "$deb_file")"
        fi
        
        # Clean up
        rm -rf "$TEMP_DIR"
    fi
done

echo "[SUCCESS] Firmware injection complete!"
echo "[INFO] Firmware files in ISO: $(find "$DEST_DIR" -type f | wc -l)"
