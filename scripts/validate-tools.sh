#!/bin/bash
# Tool validation script for Proxmox ISO Pipeline
# This script validates that all required tools exist and have execution rights
# before attempting to run the ISO build pipeline.

# Don't exit on error - we want to continue validation even if checks fail
set +e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters for validation results
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  Proxmox ISO Pipeline Tool Validator${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_section() {
    echo -e "\n${CYAN}--- $1 ---${NC}"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASS_COUNT++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAIL_COUNT++))
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARN_COUNT++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if a command exists
check_command() {
    local cmd="$1"
    local description="$2"
    local required="${3:-true}"
    
    if command -v "$cmd" &> /dev/null; then
        local version=""
        case "$cmd" in
            docker)
                version=$(docker --version 2>/dev/null | head -1)
                ;;
            python|python3|python3.*)
                version=$($cmd --version 2>/dev/null | head -1)
                ;;
            wget|curl)
                version=$($cmd --version 2>/dev/null | head -1)
                ;;
            xorriso)
                version=$(xorriso --version 2>/dev/null | head -1)
                ;;
            *)
                version="found"
                ;;
        esac
        print_pass "$description: $cmd ($version)"
        return 0
    else
        if [ "$required" = "true" ]; then
            print_fail "$description: $cmd not found"
        else
            print_warn "$description: $cmd not found (optional)"
        fi
        return 1
    fi
}

# Check if a file exists and is executable
check_executable() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        if [ -x "$file" ]; then
            print_pass "$description: $file (executable)"
            return 0
        else
            print_warn "$description: $file exists but not executable"
            return 1
        fi
    else
        print_fail "$description: $file not found"
        return 1
    fi
}

# Check if a directory exists and is writable
check_directory() {
    local dir="$1"
    local description="$2"
    local create="${3:-false}"
    
    if [ -d "$dir" ]; then
        if [ -w "$dir" ]; then
            print_pass "$description: $dir (writable)"
            return 0
        else
            print_fail "$description: $dir exists but not writable"
            return 1
        fi
    else
        if [ "$create" = "true" ]; then
            if mkdir -p "$dir" 2>/dev/null; then
                print_pass "$description: $dir (created)"
                return 0
            else
                print_fail "$description: $dir cannot be created"
                return 1
            fi
        else
            print_warn "$description: $dir does not exist"
            return 1
        fi
    fi
}

# Check Docker permissions
check_docker_permissions() {
    print_section "Docker Permissions"
    
    if docker info &> /dev/null; then
        print_pass "Docker daemon accessible"
        
        # Check if we can run containers
        if docker run --rm hello-world &> /dev/null; then
            print_pass "Can run Docker containers"
        else
            print_fail "Cannot run Docker containers"
        fi
        
        # Check if we can run privileged containers (needed for ISO mounting)
        if docker run --rm --privileged alpine:latest true &> /dev/null; then
            print_pass "Can run privileged Docker containers"
        else
            print_warn "Cannot run privileged containers (may affect ISO mounting)"
        fi
    else
        print_fail "Docker daemon not accessible (permission denied or not running)"
    fi
}

# Check disk space
check_disk_space() {
    local min_space_gb="${1:-20}"
    local dir="${2:-.}"
    
    # Get available space in GB using --output for more reliable parsing
    # Falls back to traditional method if --output is not supported
    local available_gb
    if available_gb=$(df --output=avail -BG "$dir" 2>/dev/null | tail -1 | tr -d ' G'); then
        :  # Success with --output option
    else
        # Fallback for systems without --output support
        available_gb=$(df -BG "$dir" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
    fi
    
    if [ -n "$available_gb" ] && [ "$available_gb" -eq "$available_gb" ] 2>/dev/null; then
        if [ "$available_gb" -ge "$min_space_gb" ]; then
            print_pass "Disk space: ${available_gb}GB available (minimum: ${min_space_gb}GB)"
        else
            print_fail "Disk space: ${available_gb}GB available (minimum: ${min_space_gb}GB required)"
        fi
    else
        print_warn "Could not determine available disk space"
    fi
}

# Check network connectivity
check_network() {
    print_section "Network Connectivity"
    
    # Check general internet connectivity using DNS (more reliable in corporate environments)
    if curl -s --connect-timeout 5 http://deb.debian.org/debian/ > /dev/null 2>&1 || \
       ping -c 1 -W 5 8.8.8.8 > /dev/null 2>&1; then
        print_pass "Internet connectivity available"
    else
        print_warn "Internet connectivity may be limited"
    fi
    
    # Check Proxmox enterprise repository
    if curl -s --connect-timeout 5 -I https://enterprise.proxmox.com > /dev/null 2>&1; then
        print_pass "Proxmox enterprise repository reachable"
    else
        print_warn "Proxmox enterprise repository not reachable (may need subscription)"
    fi
    
    # Check Debian repositories
    if curl -s --connect-timeout 5 -I http://deb.debian.org/debian/ > /dev/null 2>&1; then
        print_pass "Debian repositories reachable"
    else
        print_fail "Debian repositories not reachable"
    fi
}

# Main validation function
main() {
    print_header
    
    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    print_info "Project root: $PROJECT_ROOT"
    print_info "Script directory: $SCRIPT_DIR"
    
    # Section 1: Required System Commands
    print_section "Required System Commands"
    check_command "bash" "Bash shell"
    check_command "sudo" "Sudo command"
    check_command "wget" "Wget downloader"
    check_command "curl" "Curl HTTP client"
    check_command "bc" "Calculator for timing" "false"
    
    # Section 2: Docker Tools
    print_section "Docker Tools"
    check_command "docker" "Docker engine"
    if command -v docker &> /dev/null; then
        if docker compose version &> /dev/null; then
            print_pass "Docker Compose V2: $(docker compose version --short 2>/dev/null)"
        else
            print_fail "Docker Compose V2 not available"
        fi
    fi
    
    # Section 3: ISO Building Tools (may be in container)
    print_section "ISO Building Tools (host or container)"
    check_command "xorriso" "ISO creation tool" "false"
    check_command "genisoimage" "ISO generation" "false"
    check_command "isolinux" "BIOS bootloader" "false"
    check_command "dpkg-deb" "Debian package tool" "false"
    check_command "mksquashfs" "Squashfs creation tool" "false"
    
    # Section 4: Python Environment
    print_section "Python Environment"
    check_command "python3" "Python 3" "false"
    # Check for Python 3.11+ (required for this project)
    if command -v python3 &> /dev/null; then
        local py_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
        if [ -n "$py_version" ]; then
            local py_major=$(echo "$py_version" | cut -d. -f1)
            local py_minor=$(echo "$py_version" | cut -d. -f2)
            if [ "$py_major" -ge 3 ] && [ "$py_minor" -ge 11 ]; then
                print_pass "Python version $py_version meets minimum requirement (3.11+)"
            else
                print_warn "Python version $py_version is below recommended 3.11+"
            fi
        fi
    fi
    check_command "pip3" "Pip package manager" "false"
    
    # Section 5: Project Scripts
    print_section "Project Scripts"
    check_executable "$SCRIPT_DIR/build-iso.sh" "Main build script"
    check_executable "$SCRIPT_DIR/download-firmware.sh" "Firmware download script"
    check_executable "$SCRIPT_DIR/inject-firmware.sh" "Firmware injection script"
    check_executable "$SCRIPT_DIR/validate-tools.sh" "This validation script"
    
    # Section 6: Docker Files
    print_section "Docker Configuration"
    if [ -f "$PROJECT_ROOT/docker/Dockerfile" ]; then
        print_pass "Dockerfile exists: $PROJECT_ROOT/docker/Dockerfile"
    else
        print_fail "Dockerfile not found"
    fi
    
    if [ -f "$PROJECT_ROOT/docker/entrypoint.sh" ]; then
        if [ -x "$PROJECT_ROOT/docker/entrypoint.sh" ]; then
            print_pass "Entrypoint script: $PROJECT_ROOT/docker/entrypoint.sh (executable)"
        else
            print_warn "Entrypoint script exists but not executable"
        fi
    else
        print_fail "Entrypoint script not found"
    fi
    
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        print_pass "Docker Compose file exists"
    else
        print_fail "Docker Compose file not found"
    fi
    
    # Section 7: Project Directories
    print_section "Project Directories"
    check_directory "$PROJECT_ROOT/output" "Output directory" "true"
    check_directory "$PROJECT_ROOT/work" "Work directory" "true"
    check_directory "$PROJECT_ROOT/firmware-cache" "Firmware cache" "true"
    check_directory "$PROJECT_ROOT/config" "Config directory"
    check_directory "$PROJECT_ROOT/src" "Source directory"
    
    # Section 8: Configuration Files
    print_section "Configuration Files"
    if [ -f "$PROJECT_ROOT/config/firmware-sources.json" ]; then
        print_pass "Firmware sources config exists"
    else
        print_warn "Firmware sources config not found (will use defaults)"
    fi
    
    if [ -f "$PROJECT_ROOT/config/preseed.cfg" ]; then
        print_pass "Preseed config exists"
    else
        print_warn "Preseed config not found"
    fi
    
    if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
        print_pass "Python project config exists"
    else
        print_fail "Python project config not found"
    fi
    
    # Section 9: Docker Permissions
    if command -v docker &> /dev/null; then
        check_docker_permissions
    fi
    
    # Section 10: Disk Space
    print_section "System Resources"
    check_disk_space 10 "$PROJECT_ROOT"
    
    # Section 11: Network
    check_network
    
    # Summary
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}           Validation Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Passed:${NC}   $PASS_COUNT"
    echo -e "${YELLOW}Warnings:${NC} $WARN_COUNT"
    echo -e "${RED}Failed:${NC}   $FAIL_COUNT"
    echo -e "${BLUE}========================================${NC}"
    
    if [ "$FAIL_COUNT" -gt 0 ]; then
        echo -e "\n${RED}[ERROR]${NC} Some required tools or configurations are missing."
        echo -e "${YELLOW}Please fix the failed checks before running the ISO build.${NC}"
        return 1
    elif [ "$WARN_COUNT" -gt 0 ]; then
        echo -e "\n${YELLOW}[WARNING]${NC} Some optional tools are missing."
        echo -e "${GREEN}The build may still work if running inside Docker.${NC}"
        return 0
    else
        echo -e "\n${GREEN}[SUCCESS]${NC} All validations passed!"
        echo -e "${GREEN}You are ready to build the ISO.${NC}"
        return 0
    fi
}

# Run main function
main "$@"
