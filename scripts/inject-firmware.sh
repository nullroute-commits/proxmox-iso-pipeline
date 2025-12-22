#!/bin/bash
# Firmware injection script

set -e

ISO_ROOT="${1:-./work/iso_root}"
FIRMWARE_DIR="${2:-./firmware-cache}"

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

start_timer "total_firmware_injection"

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
start_timer "create_firmware_dir"
DEST_DIR="$ISO_ROOT/firmware"
mkdir -p "$DEST_DIR"
stop_timer "create_firmware_dir"

# Extract and copy firmware from .deb packages
for deb_file in "$FIRMWARE_DIR"/*.deb; do
    if [ -f "$deb_file" ]; then
        package_name=$(basename "$deb_file" .deb)
        start_timer "inject_$package_name"
        echo "[INFO] Processing: $(basename "$deb_file")"
        
        # Create temporary extraction directory
        TEMP_DIR=$(mktemp -d)
        
        # Extract .deb package
        dpkg-deb -x "$deb_file" "$TEMP_DIR" 2>/dev/null || {
            echo "[WARNING] Failed to extract: $(basename "$deb_file")"
            rm -rf "$TEMP_DIR"
            stop_timer "inject_$package_name"
            continue
        }
        
        # Copy firmware files if they exist
        if [ -d "$TEMP_DIR/lib/firmware" ]; then
            cp -r "$TEMP_DIR/lib/firmware/"* "$DEST_DIR/" 2>/dev/null || true
            echo "[SUCCESS] Copied firmware from: $(basename "$deb_file")"
        fi
        
        # Clean up
        rm -rf "$TEMP_DIR"
        stop_timer "inject_$package_name"
    fi
done

stop_timer "total_firmware_injection"
echo "[SUCCESS] Firmware injection complete!"
echo "[INFO] Firmware files in ISO: $(find "$DEST_DIR" -type f | wc -l)"

print_timing_summary
