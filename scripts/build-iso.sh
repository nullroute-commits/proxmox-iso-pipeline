#!/bin/bash
# Main ISO build script

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

# Function to validate tools before building
validate_tools() {
    start_timer "validate_tools"
    print_info "Validating required tools and permissions..."
    
    if [ -x "$SCRIPT_DIR/validate-tools.sh" ]; then
        if ! "$SCRIPT_DIR/validate-tools.sh"; then
            print_error "Tool validation failed. Please fix the issues above."
            stop_timer "validate_tools"
            exit 1
        fi
    else
        print_warning "Validation script not found or not executable, running basic checks..."
        
        # Basic Docker check
        if ! command -v docker &> /dev/null; then
            print_error "Docker is not installed or not in PATH"
            exit 1
        fi
        
        # Basic Docker Compose check
        if ! docker compose version &> /dev/null; then
            print_error "Docker Compose V2 is not installed"
            exit 1
        fi
        
        # Check Docker daemon
        if ! docker info &> /dev/null; then
            print_error "Docker daemon is not accessible"
            exit 1
        fi
    fi
    
    stop_timer "validate_tools"
    print_success "Tool validation passed"
}

# Configuration
PROXMOX_VERSION="${PROXMOX_VERSION:-9.1}"
DEBIAN_RELEASE="${DEBIAN_RELEASE:-trixie}"
INCLUDE_NVIDIA="${INCLUDE_NVIDIA:-true}"
INCLUDE_AMD="${INCLUDE_AMD:-true}"
INCLUDE_INTEL="${INCLUDE_INTEL:-true}"
SKIP_VALIDATION="${SKIP_VALIDATION:-false}"
BUILD_MODE="${BUILD_MODE:-docker}"  # docker or local

print_info "Proxmox ISO Builder"
print_info "==================="
print_info "Proxmox Version: $PROXMOX_VERSION"
print_info "Debian Release: $DEBIAN_RELEASE"
print_info "Include NVIDIA: $INCLUDE_NVIDIA"
print_info "Include AMD: $INCLUDE_AMD"
print_info "Include Intel: $INCLUDE_INTEL"
print_info "Build Mode: $BUILD_MODE"
print_info ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose V2 is not installed"
    print_info "Please install Docker Compose V2 or upgrade Docker Desktop"
    exit 1
fi

# Function to build Docker image
build_image() {
    start_timer "build_docker_image"
    print_info "Building Docker image..."
    docker compose build builder
    stop_timer "build_docker_image"
    print_success "Docker image built successfully"
}

# Function to run linter
run_linter() {
    start_timer "run_linter"
    print_info "Running code quality checks..."
    docker compose run --rm linter
    stop_timer "run_linter"
    print_success "Code quality checks passed"
}

# Function to build ISO
build_iso() {
    start_timer "build_iso"
    print_info "Starting ISO build process..."
    
    # Prepare build arguments
    BUILD_ARGS="--proxmox-version $PROXMOX_VERSION --debian-release $DEBIAN_RELEASE"
    
    if [ "$INCLUDE_NVIDIA" != "true" ]; then
        BUILD_ARGS="$BUILD_ARGS --no-nvidia"
    fi
    
    if [ "$INCLUDE_AMD" != "true" ]; then
        BUILD_ARGS="$BUILD_ARGS --no-amd"
    fi
    
    if [ "$INCLUDE_INTEL" != "true" ]; then
        BUILD_ARGS="$BUILD_ARGS --no-intel"
    fi
    
    # Run builder
    docker compose run --rm builder build $BUILD_ARGS
    stop_timer "build_iso"
    print_success "ISO build completed"
}

# Function to download firmware packages locally
download_firmware_local() {
    start_timer "download_firmware"
    print_info "Downloading firmware packages..."
    
    if [ -x "$SCRIPT_DIR/download-firmware.sh" ]; then
        "$SCRIPT_DIR/download-firmware.sh"
    else
        print_error "Download firmware script not found: $SCRIPT_DIR/download-firmware.sh"
        stop_timer "download_firmware"
        return 1
    fi
    
    stop_timer "download_firmware"
    print_success "Firmware download completed"
}

# Function to inject firmware into ISO
inject_firmware_local() {
    start_timer "inject_firmware"
    print_info "Injecting firmware into ISO..."
    
    if [ -x "$SCRIPT_DIR/inject-firmware.sh" ]; then
        sudo "$SCRIPT_DIR/inject-firmware.sh" "$PROJECT_ROOT/work/iso_root" "$PROJECT_ROOT/firmware-cache"
    else
        print_error "Inject firmware script not found: $SCRIPT_DIR/inject-firmware.sh"
        stop_timer "inject_firmware"
        return 1
    fi
    
    stop_timer "inject_firmware"
    print_success "Firmware injection completed"
}

# Function to build early microcode
build_early_microcode_local() {
    start_timer "build_early_microcode"
    print_info "Building early microcode initramfs..."
    
    if [ -x "$SCRIPT_DIR/build-early-microcode.sh" ]; then
        sudo "$SCRIPT_DIR/build-early-microcode.sh" "$PROJECT_ROOT/work/iso_root"
    else
        print_error "Build early microcode script not found: $SCRIPT_DIR/build-early-microcode.sh"
        stop_timer "build_early_microcode"
        return 1
    fi
    
    stop_timer "build_early_microcode"
    print_success "Early microcode build completed"
}

# Function to rebuild ISO from modified contents
rebuild_iso_local() {
    start_timer "rebuild_iso"
    print_info "Rebuilding ISO..."
    
    if [ -x "$SCRIPT_DIR/rebuild-iso.sh" ]; then
        sudo "$SCRIPT_DIR/rebuild-iso.sh"
    else
        print_error "Rebuild ISO script not found: $SCRIPT_DIR/rebuild-iso.sh"
        stop_timer "rebuild_iso"
        return 1
    fi
    
    stop_timer "rebuild_iso"
    print_success "ISO rebuild completed"
}

# Function to run complete local build (firmware + microcode + rebuild)
build_local() {
    start_timer "build_local_total"
    print_info "Running local build pipeline..."
    
    # Check for required ISO root
    if [ ! -d "$PROJECT_ROOT/work/iso_root" ]; then
        print_error "ISO root not found: $PROJECT_ROOT/work/iso_root"
        print_info "Please extract a Proxmox ISO first or run the Docker build"
        stop_timer "build_local_total"
        return 1
    fi
    
    # Download firmware
    download_firmware_local || return 1
    
    # Inject firmware
    inject_firmware_local || return 1
    
    # Build early microcode
    build_early_microcode_local || return 1
    
    # Rebuild ISO
    rebuild_iso_local || return 1
    
    stop_timer "build_local_total"
    print_success "Local build completed successfully!"
}

# Main execution
main() {
    start_timer "total_execution"
    
    case "${1:-all}" in
        validate)
            validate_tools
            ;;
        build-image)
            if [ "$SKIP_VALIDATION" != "true" ]; then
                validate_tools
            fi
            build_image
            ;;
        lint)
            if [ "$SKIP_VALIDATION" != "true" ]; then
                validate_tools
            fi
            run_linter
            ;;
        build)
            if [ "$SKIP_VALIDATION" != "true" ]; then
                validate_tools
            fi
            build_iso
            ;;
        all)
            if [ "$SKIP_VALIDATION" != "true" ]; then
                validate_tools
            fi
            build_image
            run_linter
            build_iso
            ;;
        # Local build commands (no Docker required)
        download-firmware)
            download_firmware_local
            ;;
        inject-firmware)
            inject_firmware_local
            ;;
        build-microcode)
            build_early_microcode_local
            ;;
        rebuild-iso)
            rebuild_iso_local
            ;;
        local)
            build_local
            ;;
        help|--help|-h)
            echo "Proxmox ISO Builder"
            echo ""
            echo "Usage: $0 {command}"
            echo ""
            echo "Docker Build Commands:"
            echo "  validate    - Validate all required tools and permissions"
            echo "  build-image - Build Docker image only"
            echo "  lint        - Run code quality checks"
            echo "  build       - Build the ISO using Docker (requires Docker image)"
            echo "  all         - Run all Docker steps (validate, build-image, lint, build)"
            echo ""
            echo "Local Build Commands (no Docker required):"
            echo "  download-firmware - Download firmware packages"
            echo "  inject-firmware   - Inject firmware into ISO root"
            echo "  build-microcode   - Build early microcode initramfs"
            echo "  rebuild-iso       - Rebuild ISO from modified contents"
            echo "  local             - Run complete local build pipeline"
            echo ""
            echo "  help        - Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  PROXMOX_VERSION   - Proxmox VE version (default: 9.1)"
            echo "  DEBIAN_RELEASE    - Debian release name (default: trixie)"
            echo "  INCLUDE_NVIDIA    - Include NVIDIA firmware (default: true)"
            echo "  INCLUDE_AMD       - Include AMD firmware (default: true)"
            echo "  INCLUDE_INTEL     - Include Intel firmware (default: true)"
            echo "  SKIP_VALIDATION   - Skip tool validation (default: false)"
            exit 0
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Usage: $0 {validate|build-image|lint|build|all|download-firmware|inject-firmware|build-microcode|rebuild-iso|local|help}"
            exit 1
            ;;
    esac
    
    stop_timer "total_execution"
    print_timing_summary
}

main "$@"
