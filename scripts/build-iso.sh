#!/bin/bash
# Main ISO build script

set -e

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

# Configuration
PROXMOX_VERSION="${PROXMOX_VERSION:-9.1}"
DEBIAN_RELEASE="${DEBIAN_RELEASE:-trixie}"
INCLUDE_NVIDIA="${INCLUDE_NVIDIA:-true}"
INCLUDE_AMD="${INCLUDE_AMD:-true}"
INCLUDE_INTEL="${INCLUDE_INTEL:-true}"

print_info "Proxmox ISO Builder"
print_info "==================="
print_info "Proxmox Version: $PROXMOX_VERSION"
print_info "Debian Release: $DEBIAN_RELEASE"
print_info "Include NVIDIA: $INCLUDE_NVIDIA"
print_info "Include AMD: $INCLUDE_AMD"
print_info "Include Intel: $INCLUDE_INTEL"
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

# Main execution
main() {
    start_timer "total_execution"
    
    case "${1:-all}" in
        build-image)
            build_image
            ;;
        lint)
            run_linter
            ;;
        build)
            build_iso
            ;;
        all)
            build_image
            run_linter
            build_iso
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Usage: $0 {build-image|lint|build|all}"
            exit 1
            ;;
    esac
    
    stop_timer "total_execution"
    print_timing_summary
}

main "$@"
