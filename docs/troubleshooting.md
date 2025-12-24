# Troubleshooting

> **Documentation Version:** 1.0.0  
> **Audience:** All Users  
> **Last Updated:** 2024-12-23

Common issues, solutions, and debugging tips for the Proxmox ISO Pipeline.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Build Issues](#build-issues)
- [Docker Issues](#docker-issues)
- [Firmware Issues](#firmware-issues)
- [Boot Issues](#boot-issues)
- [Post-Install Boot Issues](#post-install-boot-issues)
- [Installation Issues](#installation-issues)
- [Getting Help](#getting-help)

## Quick Diagnostics

### Health Check Script

Run this diagnostic script to identify common issues:

```bash
#!/bin/bash
echo "=== Proxmox ISO Pipeline Diagnostics ==="

# Check Docker
echo -n "Docker: "
docker --version 2>/dev/null || echo "NOT INSTALLED"

# Check Docker Compose
echo -n "Docker Compose: "
docker compose version 2>/dev/null || echo "NOT INSTALLED"

# Check disk space
echo -n "Disk Space: "
df -h . | tail -1 | awk '{print $4 " available"}'

# Check Python (if running locally)
echo -n "Python: "
python3 --version 2>/dev/null | grep -q "3.13" && python3 --version || echo "3.13.x NOT FOUND"

# Check network
echo -n "Network (Proxmox): "
status=$(curl -s -o /dev/null -w "%{http_code}" https://enterprise.proxmox.com 2>/dev/null)
[ -n "$status" ] && echo "$status" || echo "FAILED"

echo -n "Network (Debian): "
status=$(curl -s -o /dev/null -w "%{http_code}" http://deb.debian.org 2>/dev/null)
[ -n "$status" ] && echo "$status" || echo "FAILED"

# Check directories
echo "Directories:"
for dir in output work firmware-cache; do
  if [ -d "$dir" ]; then
    echo "  $dir: EXISTS ($(du -sh $dir 2>/dev/null | cut -f1))"
  else
    echo "  $dir: MISSING"
  fi
done
```

## Build Issues

### Issue: Permission Denied

**Symptoms:**
```
Failed to extract ISO: Permission denied
sudo: unable to execute /bin/mount: Permission denied
```

**Solution:**
The container needs privileged mode for ISO mounting operations.

```bash
# Using Docker Compose (already configured)
docker compose run --rm builder build

# Using Docker directly
docker run --rm --privileged \
  -v $(pwd)/output:/workspace/output \
  proxmox-iso-builder:latest build
```

### Issue: Not Enough Disk Space

**Symptoms:**
```
No space left on device
Failed to write ISO
```

**Solution:**
Ensure at least 20GB free space:

```bash
# Check available space
df -h .

# Clean up old builds
rm -rf output/* work/*

# Clean Docker system
docker system prune -af

# Clean firmware cache (will re-download)
rm -rf firmware-cache/*
```

### Issue: ISO Download Fails

**Symptoms:**
```
Failed to download ISO: Connection timed out
wget: unable to resolve host address
```

**Solutions:**

1. **Check network connectivity:**
```bash
curl -I https://enterprise.proxmox.com/iso/
```

2. **Use a mirror or custom URL:**
```bash
docker compose run --rm builder build \
  --iso-url https://mirror.example.com/proxmox-ve_9.1.iso
```

3. **Pre-download the ISO:**
```bash
# Download manually
wget -O work/proxmox-ve_9.1.iso \
  https://enterprise.proxmox.com/iso/proxmox-ve_9.1-1.iso

# The builder will use the existing file
docker compose run --rm builder build
```

### Issue: Build Hangs at "Downloading firmware"

**Symptoms:**
- Build appears stuck during firmware download
- No progress for several minutes

**Solutions:**

1. **Check apt sources:**
```bash
# Inside container
docker compose run --rm builder bash
cat /etc/apt/sources.list.d/*.list
apt-get update
```

2. **Force re-download:**
```bash
rm -rf firmware-cache/*
docker compose run --rm builder build
```

3. **Check Debian mirror status:**
```bash
curl http://deb.debian.org/debian/dists/trixie/Release
```

## Docker Issues

### Issue: Docker Not Found

**Symptoms:**
```
docker: command not found
Cannot connect to the Docker daemon
```

**Solutions:**

1. **Install Docker:**
   - Linux: https://docs.docker.com/engine/install/
   - macOS: https://docs.docker.com/desktop/mac/install/
   - Windows: https://docs.docker.com/desktop/windows/install/

2. **Start Docker daemon:**
```bash
# Linux
sudo systemctl start docker
sudo systemctl enable docker

# macOS/Windows
# Start Docker Desktop application
```

3. **Add user to docker group (Linux):**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Issue: Docker Compose Not Found

**Symptoms:**
```
docker-compose: command not found
docker compose: not a docker command
```

**Solutions:**

1. **Use Docker Compose V2:**
```bash
# Check version
docker compose version

# If not found, install plugin
# See: https://docs.docker.com/compose/install/
```

2. **Update Docker Desktop** (includes Compose V2)

### Issue: Build Context Too Large

**Symptoms:**
```
Sending build context to Docker daemon  5.2GB
```

**Solution:**
Ensure `.dockerignore` is properly configured:

```bash
# Check .dockerignore exists and contains
cat .dockerignore

# Should include:
output/
work/
firmware-cache/
venv/
__pycache__/
*.iso
```

### Issue: Multi-arch Build Fails

**Symptoms:**
```
ERROR: Multiple platforms feature is currently not supported for docker driver
```

**Solution:**
Set up Docker Buildx:

```bash
# Create buildx builder
docker buildx create --name multiarch --use

# Bootstrap with QEMU
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Verify
docker buildx inspect --bootstrap
```

## Firmware Issues

### Issue: Firmware Package Not Found

**Symptoms:**
```
Failed to download nvidia-driver: Package not found
E: Unable to locate package
```

**Solutions:**

1. **Ensure non-free sources are enabled:**
```bash
# The builder should configure this automatically
# Check manually inside container
docker compose run --rm builder bash
grep non-free /etc/apt/sources.list.d/*
```

2. **Update package lists:**
```bash
docker compose run --rm builder bash -c "apt-get update"
```

3. **Check package name:**
```bash
# Search for package
apt-cache search nvidia | grep driver
```

### Issue: Firmware Integration Fails

**Symptoms:**
```
FirmwareIntegrationError: Failed to extract package
dpkg-deb: error
```

**Solutions:**

1. **Check package integrity:**
```bash
# Re-download firmware
rm -rf firmware-cache/*
docker compose run --rm builder build
```

2. **Check disk space:**
```bash
df -h firmware-cache/
```

### Issue: Specific Vendor Firmware Fails

**Symptoms:**
```
Warning: Failed to download NVIDIA firmware: ...
```

**Solution:**
Build without the problematic firmware:

```bash
# Skip NVIDIA firmware
docker compose run --rm builder build --no-nvidia

# Skip AMD firmware
docker compose run --rm builder build --no-amd

# Skip Intel firmware
docker compose run --rm builder build --no-intel
```

## Boot Issues

### Issue: ISO Won't Boot (Black Screen)

**Symptoms:**
- System shows nothing after selecting ISO boot
- Black screen after boot loader

**Solutions:**

1. **Check boot mode compatibility:**
   - UEFI systems: Should work with default ISO
   - Legacy BIOS: May need to disable Secure Boot

2. **Try different boot mode:**
```
BIOS Setup → Boot → Boot Mode
Change from UEFI to Legacy or vice versa
```

3. **Test in VM first:**
```bash
# UEFI mode test
qemu-system-x86_64 \
  -bios /usr/share/ovmf/OVMF.fd \
  -cdrom output/proxmox-ve_9.1_custom.iso \
  -m 4G

# BIOS mode test
qemu-system-x86_64 \
  -cdrom output/proxmox-ve_9.1_custom.iso \
  -m 4G
```

### Issue: Secure Boot Failure

**Symptoms:**
```
Verification failed: (0x1A) Security Violation
```

**Solutions:**

1. **Disable Secure Boot temporarily:**
```
BIOS Setup → Security → Secure Boot → Disabled
```

2. **The ISO supports Secure Boot** via signed GRUB, but some systems may still reject it

3. **Re-enable after installation** if desired

### Issue: USB Won't Boot

**Symptoms:**
- USB device not recognized
- Boot menu doesn't show USB

**Solutions:**

1. **Verify USB writing:**
```bash
# Check USB write completed
sync

# Verify ISO was written correctly (Linux)
cmp output/proxmox-ve_9.1_custom.iso /dev/sdX
```

2. **Use DD mode in Rufus (Windows):**
   - Select "DD Image" when prompted
   - NOT "ISO Image"

3. **Check USB port:**
   - Try USB 2.0 port instead of 3.0
   - Try different USB device

### Issue: Boot File Missing Error

**Symptoms:**
```
Missing boot image file: efi.img
```

**Solution:**
This indicates the source ISO may be corrupted or incompatible.

```bash
# Re-download source ISO
rm -f work/proxmox-ve_*.iso
docker compose run --rm builder build
```

## Post-Install Boot Issues

> **Note:** As of the latest pipeline version, firmware is automatically injected into the 
> `pve-base.squashfs` image, which means the installed system should have all firmware 
> available at first boot. The issues below apply to older ISOs or ISOs built without 
> the squashfs injection step.

### Issue: System Hangs After Loading Initramfs

**Symptoms:**
- Installation completes successfully
- After removing install media, system starts booting
- Kernel loads, initramfs loads
- System hangs with no further output (black screen or stuck on "Loading initial ramdisk...")
- No login prompt appears

**Root Cause:**
The installed system's initramfs is missing firmware required to access the storage controller (NVMe, AHCI, RAID, SAS/HBA). This typically happens with ISOs that didn't have firmware injected into the squashfs image.

**Quick Fix (if using latest pipeline):**
Rebuild the ISO using the latest pipeline version which automatically injects firmware into the installable system image:
```bash
cd proxmox-iso-pipeline
git pull
./scripts/build-iso.sh local
```

**Manual Recovery (for older ISOs):**

1. **Boot from the custom ISO again**

2. **Access a shell** - At the installer menu, press `Ctrl+Alt+F2` to get a terminal

3. **Identify and mount your root partition:**
```bash
# List available partitions
lsblk
fdisk -l

# Mount root partition (examples for different setups)
# NVMe:
mount /dev/nvme0n1p2 /mnt

# SATA:
mount /dev/sda2 /mnt

# LVM (most common for Proxmox):
vgchange -ay  # Activate volume groups
mount /dev/mapper/pve-root /mnt
```

4. **Bind mount required filesystems:**
```bash
mount --bind /dev /mnt/dev
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
mount --bind /run /mnt/run
```

5. **Chroot into the installed system:**
```bash
chroot /mnt /bin/bash
```

6. **Copy firmware from the installer media:**
```bash
# The ISO should be mounted at /cdrom or similar
# If not, mount it manually:
mkdir -p /mnt2
mount /dev/sr0 /mnt2  # CD/DVD drive
# or for USB:
mount /dev/sdb1 /mnt2

# Copy all firmware
cp -r /mnt2/firmware/* /lib/firmware/
# or if using /cdrom:
cp -r /cdrom/firmware/* /lib/firmware/
```

7. **Rebuild the initramfs:**
```bash
update-initramfs -u -k all
```

8. **Exit and reboot:**
```bash
exit
umount -R /mnt
reboot
```

**Prevention for Future Installs:**

After a fresh install from the custom ISO, always run these commands before rebooting:

```bash
# From the installer shell (Ctrl+Alt+F2)
# Mount the newly installed system
mount /dev/mapper/pve-root /mnt  # Adjust as needed

# Copy firmware
cp -r /cdrom/firmware/* /mnt/lib/firmware/

# Chroot and rebuild initramfs
mount --bind /dev /mnt/dev
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
chroot /mnt update-initramfs -u -k all
umount /mnt/dev /mnt/proc /mnt/sys
umount /mnt
```

### Issue: System Boots But Missing Hardware

**Symptoms:**
- System boots to login
- Some hardware (GPU, network, storage controller) not detected
- `dmesg` shows firmware loading errors

**Solution:**
```bash
# Copy firmware from the ISO to the running system
# Insert/mount the custom ISO
mount /dev/sr0 /mnt
cp -r /mnt/firmware/* /lib/firmware/
umount /mnt

# Reload modules or reboot
modprobe -r <driver_name>
modprobe <driver_name>
# or
reboot
```

## Installation Issues

### Issue: Driver Not Loading After Install

**Symptoms:**
- NVIDIA/AMD/Intel drivers not active after Proxmox installation
- `nvidia-smi` shows error

**Solutions:**

1. **Verify firmware was installed:**
```bash
# On installed Proxmox system
ls /lib/firmware/nvidia/
ls /lib/firmware/amdgpu/
```

2. **Install driver userspace tools:**
```bash
# NVIDIA
apt update
apt install nvidia-driver

# Check
nvidia-smi
```

3. **Rebuild initramfs:**
```bash
update-initramfs -u
reboot
```

### Issue: Network Not Working During Install

**Symptoms:**
- No network interfaces detected
- WiFi not available

**Solutions:**

1. **Use wired connection** if possible during install

2. **Check if firmware was included:**
```bash
# Before building, ensure network firmware is included
cat config/firmware-sources.json
```

3. **Add network firmware packages:**
```json
{
  "freeware": [
    "firmware-linux-free",
    "firmware-misc-nonfree",
    "firmware-linux-nonfree",
    "firmware-realtek",
    "firmware-iwlwifi"
  ]
}
```

## Debug Mode

### Enable Verbose Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Or in Python
python -m src.builder --proxmox-version 9.1 -v
```

### Inspect Build Artifacts

```bash
# Check extracted ISO contents
ls -la work/iso_root/

# Check firmware that was integrated
ls -la work/iso_root/firmware/

# Check boot files
ls -la work/iso_root/isolinux/
ls -la work/iso_root/efi.img
```

### Container Debug

```bash
# Enter container interactively
docker compose run --rm builder bash

# Inside container
python -c "from src.builder import ProxmoxISOBuilder; print('OK')"
apt-get update
apt-cache search nvidia
```

## Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Review the logs:**
   ```bash
   docker compose logs builder
   ```
3. **Run diagnostics script** (above)
4. **Search existing issues:**
   https://github.com/nullroute-commits/proxmox-iso-pipeline/issues

### Reporting Issues

Include this information when opening an issue:

```markdown
**Environment:**
- OS: [e.g., Ubuntu 22.04, Windows 11, macOS 14]
- Docker version: [output of `docker --version`]
- Docker Compose version: [output of `docker compose version`]

**Configuration:**
- Proxmox version: [e.g., 9.1]
- Firmware options: [NVIDIA: yes/no, AMD: yes/no, Intel: yes/no]
- Custom config: [yes/no]

**Steps to Reproduce:**
1. [First step]
2. [Second step]
3. [...]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Logs:**
```
[Paste relevant log output]
```

**Additional Context:**
[Any other relevant information]
```

### Support Channels

- **GitHub Issues**: Bug reports and feature requests
  https://github.com/nullroute-commits/proxmox-iso-pipeline/issues

- **GitHub Discussions**: Questions and community support
  https://github.com/nullroute-commits/proxmox-iso-pipeline/discussions

- **Documentation**: This docs/ directory

## Next Steps

- [User Guide](user-guide.md) - Basic usage
- [Configuration Reference](configuration.md) - All options
- [Architecture](architecture.md) - System design

---

*[Back to Documentation Index](README.md)*
