#!/bin/bash
# Firmware download script

set -e

DEBIAN_RELEASE="${DEBIAN_RELEASE:-trixie}"
CACHE_DIR="${FIRMWARE_CACHE:-./firmware-cache}"

# Color output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Timing variables
declare -A TIMING_START
declare -A TIMING_END
declare -a TIMING_ORDER

# Function to start timing
start_timer() {
    local name="$1"
    TIMING_START["$name"]=$(date +%s.%N)
    TIMING_ORDER+=("$name")
}

# Function to stop timing
stop_timer() {
    local name="$1"
    TIMING_END["$name"]=$(date +%s.%N)
    local start="${TIMING_START[$name]}"
    local end="${TIMING_END[$name]}"
    local duration=$(echo "$end - $start" | bc)
    echo -e "${CYAN}[PERF]${NC} $name: ${duration}s"
}

# Function to print performance summary
print_timing_summary() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}       Performance Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    local total=0
    for name in "${TIMING_ORDER[@]}"; do
        local start="${TIMING_START[$name]}"
        local end="${TIMING_END[$name]}"
        if [ -n "$start" ] && [ -n "$end" ]; then
            local duration=$(echo "$end - $start" | bc)
            total=$(echo "$total + $duration" | bc)
            printf "${CYAN}%-30s${NC} %10.2fs\n" "$name:" "$duration"
        fi
    done
    
    echo -e "${BLUE}----------------------------------------${NC}"
    printf "${GREEN}%-30s${NC} %10.2fs\n" "Total:" "$total"
    echo -e "${BLUE}========================================${NC}\n"
}

start_timer "total_firmware_download"

echo "[INFO] Downloading firmware packages..."
echo "[INFO] Debian Release: $DEBIAN_RELEASE"
echo "[INFO] Cache Directory: $CACHE_DIR"

# Create cache directory
mkdir -p "$CACHE_DIR"

# Function to download package
download_package() {
    local package_name="$1"
    local cache_file="$CACHE_DIR/${package_name}.deb"
    
    start_timer "download_$package_name"
    
    if [ -f "$cache_file" ]; then
        echo "[INFO] Package already cached: $package_name"
        stop_timer "download_$package_name"
        return 0
    fi
    
    echo "[INFO] Downloading: $package_name"
    
    cd "$CACHE_DIR"
    apt-get download -t "$DEBIAN_RELEASE" "$package_name" 2>/dev/null || {
        echo "[WARNING] Failed to download: $package_name"
        stop_timer "download_$package_name"
        cd - > /dev/null
        return 1
    }
    cd - > /dev/null
    
    stop_timer "download_$package_name"
    echo "[SUCCESS] Downloaded: $package_name"
}

# Freeware firmware
start_timer "freeware_firmware"
echo "[INFO] Downloading freeware firmware..."
download_package "firmware-linux-free"
download_package "firmware-misc-nonfree"
download_package "firmware-linux-nonfree"
stop_timer "freeware_firmware"

# NVIDIA firmware
if [ "${INCLUDE_NVIDIA:-true}" = "true" ]; then
    start_timer "nvidia_firmware"
    echo "[INFO] Downloading NVIDIA firmware..."
    download_package "firmware-nvidia-graphics" || true
    stop_timer "nvidia_firmware"
fi

# AMD firmware
if [ "${INCLUDE_AMD:-true}" = "true" ]; then
    start_timer "amd_firmware"
    echo "[INFO] Downloading AMD firmware..."
    download_package "firmware-amd-graphics" || true
    download_package "amd64-microcode" || true
    stop_timer "amd_firmware"
fi

# Intel firmware
if [ "${INCLUDE_INTEL:-true}" = "true" ]; then
    start_timer "intel_firmware"
    echo "[INFO] Downloading Intel firmware..."
    download_package "intel-microcode" || true
    download_package "firmware-intel-sound" || true
    stop_timer "intel_firmware"
fi

stop_timer "total_firmware_download"
echo "[SUCCESS] Firmware download complete!"

print_timing_summary
