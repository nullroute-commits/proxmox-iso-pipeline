#!/bin/bash
# Firmware download script

set -e

DEBIAN_RELEASE="${DEBIAN_RELEASE:-trixie}"
CACHE_DIR="${FIRMWARE_CACHE:-./firmware-cache}"

echo "[INFO] Downloading firmware packages..."
echo "[INFO] Debian Release: $DEBIAN_RELEASE"
echo "[INFO] Cache Directory: $CACHE_DIR"

# Create cache directory
mkdir -p "$CACHE_DIR"

# Function to download package
download_package() {
    local package_name="$1"
    local cache_file="$CACHE_DIR/${package_name}.deb"
    
    if [ -f "$cache_file" ]; then
        echo "[INFO] Package already cached: $package_name"
        return 0
    fi
    
    echo "[INFO] Downloading: $package_name"
    
    cd "$CACHE_DIR"
    apt-get download -t "$DEBIAN_RELEASE" "$package_name" 2>/dev/null || {
        echo "[WARNING] Failed to download: $package_name"
        return 1
    }
    cd - > /dev/null
    
    echo "[SUCCESS] Downloaded: $package_name"
}

# Freeware firmware
echo "[INFO] Downloading freeware firmware..."
download_package "firmware-linux-free"
download_package "firmware-misc-nonfree"
download_package "firmware-linux-nonfree"

# NVIDIA firmware
if [ "${INCLUDE_NVIDIA:-true}" = "true" ]; then
    echo "[INFO] Downloading NVIDIA firmware..."
    download_package "firmware-nvidia-graphics" || true
fi

# AMD firmware
if [ "${INCLUDE_AMD:-true}" = "true" ]; then
    echo "[INFO] Downloading AMD firmware..."
    download_package "firmware-amd-graphics" || true
    download_package "amd64-microcode" || true
fi

# Intel firmware
if [ "${INCLUDE_INTEL:-true}" = "true" ]; then
    echo "[INFO] Downloading Intel firmware..."
    download_package "intel-microcode" || true
    download_package "firmware-intel-sound" || true
fi

echo "[SUCCESS] Firmware download complete!"
