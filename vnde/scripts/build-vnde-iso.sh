#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "[ERR ] Hay chay script bang sudo/root."
  exit 1
fi

ISO_IN="${1:-}"
ISO_OUT="${2:-$PWD/VNOS-24.04.3.iso}"
# Keep build artifacts outside source tree to avoid recursive rsync.
WORKDIR="${WORKDIR:-/tmp/.build-vnde-iso}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ -z "$ISO_IN" || ! -f "$ISO_IN" ]]; then
  echo "Usage: sudo $0 /duongdan/ubuntu-24.04.3-desktop-amd64.iso [output.iso]"
  exit 1
fi

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERR ] Thieu lenh: $1"
    exit 1
  }
}

for c in xorriso unsquashfs mksquashfs rsync chroot sed awk cpio file; do
  need_cmd "$c"
done

replace_text_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  sed -i \
    -e "s/Ubuntu/VNOS/g" \
    -e "s/ubuntu/VNOS/g" \
    -e "s/UBUNTU/VNOS/g" \
    "$f" || true
}

replace_text_tree() {
  local root="$1"
  [[ -d "$root" ]] || return 0
  while IFS= read -r f; do
    replace_text_file "$f"
  done < <(grep -IlR --binary-files=without-match -E 'Ubuntu|ubuntu|UBUNTU' "$root" 2>/dev/null || true)
}

patch_initrd_branding() {
  local initrd_file="$1"
  local logo_png="$2"
  [[ -f "$initrd_file" ]] || return 0

  local initrd_type dec_cmd enc_cmd
  initrd_type="$(file -b "$initrd_file" || true)"
  case "$initrd_type" in
    *Zstandard*)
      dec_cmd="zstd -dc"
      enc_cmd="zstd -q -19 -T0"
      ;;
    *XZ*compressed*)
      dec_cmd="xz -dc"
      enc_cmd="xz -zc -9e"
      ;;
    *gzip*compressed*|*gzip*)
      dec_cmd="gzip -dc"
      enc_cmd="gzip -9c"
      ;;
    *cpio*)
      dec_cmd="cat"
      enc_cmd="cat"
      ;;
    *)
      echo "[WARN] Bo qua patch initrd khong ro dinh dang: $initrd_file ($initrd_type)"
      return 0
      ;;
  esac

  local d
  d="$(mktemp -d "$WORKDIR/initrd.XXXXXX")"
  mkdir -p "$d/root"

  # shellcheck disable=SC2086
  if ! eval "$dec_cmd \"$initrd_file\"" | (cd "$d/root" && cpio -id --quiet --no-absolute-filenames); then
    echo "[WARN] Khong giai nen duoc initrd: $initrd_file"
    rm -rf "$d"
    return 0
  fi

  replace_text_tree "$d/root/etc"
  replace_text_tree "$d/root/usr/share"

  if [[ -f "$logo_png" ]]; then
    while IFS= read -r f; do
      cp "$logo_png" "$f" || true
    done < <(find "$d/root/usr/share" -type f \( -name '*ubuntu*logo*.png' -o -name '*ubuntu*.png' -o -name 'watermark.png' -o -name 'bgrt-fallback.png' \) 2>/dev/null || true)
  fi

  if [[ -f "$d/root/etc/alternatives/default.plymouth" ]]; then
    sed -i \
      -e 's/ubuntu/VNOS/g' \
      -e 's/Ubuntu/VNOS/g' \
      "$d/root/etc/alternatives/default.plymouth" || true
  fi

  # Repack initrd with the same compression family.
  rm -f "$initrd_file"
  # shellcheck disable=SC2086
  (cd "$d/root" && find . -print0 | cpio --null -o -H newc --quiet | eval "$enc_cmd > \"$initrd_file\"")
  rm -rf "$d"
}

cleanup() {
  set +e
  if mountpoint -q "$WORKDIR/chroot/dev"; then umount -lf "$WORKDIR/chroot/dev"; fi
  if mountpoint -q "$WORKDIR/chroot/proc"; then umount -lf "$WORKDIR/chroot/proc"; fi
  if mountpoint -q "$WORKDIR/chroot/sys"; then umount -lf "$WORKDIR/chroot/sys"; fi
}
trap cleanup EXIT

echo "[INFO] Dung workdir: $WORKDIR"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR/iso" "$WORKDIR/mnt" "$WORKDIR/chroot"

echo "[INFO] Extract ISO..."
xorriso -osirrox on -indev "$ISO_IN" -extract / "$WORKDIR/iso" >/dev/null

SQFS=""
# Ubuntu 24.04.3 installer/live media can use different squashfs names.
if [[ -f "$WORKDIR/iso/casper/filesystem.squashfs" ]]; then
  SQFS="$WORKDIR/iso/casper/filesystem.squashfs"
else
  # Prefer explicit live image names first.
  for cand in \
    "$WORKDIR/iso/casper/minimal.standard.live.squashfs" \
    "$WORKDIR/iso/casper/minimal.live.squashfs"; do
    if [[ -f "$cand" ]]; then
      SQFS="$cand"
      break
    fi
  done
fi

if [[ -z "$SQFS" ]]; then
  # Fallback: choose the largest *.squashfs under casper (excluding .gpg sidecars).
  SQFS="$(find "$WORKDIR/iso/casper" -maxdepth 1 -type f -name '*.squashfs' ! -name '*.gpg' -printf '%s %p\n' 2>/dev/null | sort -nr | head -n1 | awk '{print $2}')"
fi

if [[ -z "$SQFS" || ! -f "$SQFS" ]]; then
  echo "[ERR ] Khong tim thay file .squashfs trong ISO (casper/*)."
  exit 1
fi
echo "[INFO] Dung squashfs: $SQFS"

echo "[INFO] Unsquashfs..."
unsquashfs -f -d "$WORKDIR/chroot" "$SQFS" >/dev/null

echo "[INFO] Mount chroot helpers..."
mkdir -p "$WORKDIR/chroot/dev" "$WORKDIR/chroot/proc" "$WORKDIR/chroot/sys" "$WORKDIR/chroot/etc"
mount --bind /dev "$WORKDIR/chroot/dev"
mount -t proc /proc "$WORKDIR/chroot/proc"
mount -t sysfs /sys "$WORKDIR/chroot/sys"
cp /etc/resolv.conf "$WORKDIR/chroot/etc/resolv.conf"

echo "[INFO] Copy VNDE source vao image..."
mkdir -p "$WORKDIR/chroot/usr/local/share/vnde"
rsync -a --delete \
  --one-file-system \
  --exclude ".git" \
  --exclude "/.build-vnde-iso/" \
  --exclude ".build-vnde-iso/" \
  --exclude ".build-vnde-iso/***" \
  --exclude "/.build-vnde-iso/***" \
  --exclude "*.iso" \
  --exclude "__pycache__" \
  "$ROOT_DIR/" "$WORKDIR/chroot/usr/local/share/vnde/"

echo "[INFO] Rebrand thanh VNOS..."
# Boot menu labels in ISO (live media stage)
for f in \
  "$WORKDIR/iso/boot/grub/grub.cfg" \
  "$WORKDIR/iso/boot/grub/loopback.cfg" \
  "$WORKDIR/iso/EFI/boot/grub.cfg"; do
  replace_text_file "$f"
done

# Replace installer/live text labels broadly in extracted ISO tree.
replace_text_tree "$WORKDIR/iso/.disk"
replace_text_tree "$WORKDIR/iso/boot"
replace_text_tree "$WORKDIR/iso/EFI"
replace_text_tree "$WORKDIR/iso/casper"

echo "[INFO] Patch initrd boot splash/logo..."
VNOS_BOOT_LOGO="$ROOT_DIR/assets/wallpapers/vietnam-dawn-demo.png"
while IFS= read -r initrd; do
  patch_initrd_branding "$initrd" "$VNOS_BOOT_LOGO"
done < <(find "$WORKDIR/iso/casper" -maxdepth 1 -type f -name 'initrd*' ! -name '*.sig' ! -name '*.gpg' 2>/dev/null || true)

# Disable splash/logo at early boot stage.
for f in \
  "$WORKDIR/iso/boot/grub/grub.cfg" \
  "$WORKDIR/iso/boot/grub/loopback.cfg" \
  "$WORKDIR/iso/EFI/boot/grub.cfg"; do
  [[ -f "$f" ]] || continue
  sed -i -E \
    -e 's/[[:space:]]+plymouth.enable=0//g' \
    -e 's/[[:space:]]+loglevel=[0-9]+//g' \
    -e 's/[[:space:]]+systemd.show_status=[a-z0-9]+//g' \
    -e 's/[[:space:]]+rd.udev.log_level=[0-9]+//g' \
    -e 's/[[:space:]]+vt.global_cursor_default=[0-9]+//g' \
    -e 's/(^|[[:space:]])quiet([[:space:]]|$)/ /g' \
    -e 's/(^|[[:space:]])splash([[:space:]]|$)/ /g' \
    "$f"
  sed -i -E 's/ ---/ plymouth.enable=0 nosplash loglevel=4 systemd.show_status=1 ---/g' "$f"
  sed -i -E 's/[[:space:]]+/ /g' "$f"
done

# OS identity in target live filesystem
for f in \
  "$WORKDIR/chroot/etc/os-release" \
  "$WORKDIR/chroot/usr/lib/os-release" \
  "$WORKDIR/chroot/etc/lsb-release" \
  "$WORKDIR/chroot/etc/issue" \
  "$WORKDIR/chroot/etc/issue.net"; do
  replace_text_file "$f"
done

# Replace visible Ubuntu strings in live rootfs UI and installer assets.
replace_text_tree "$WORKDIR/chroot/etc"
replace_text_tree "$WORKDIR/chroot/usr/share"

if [[ -f "$WORKDIR/chroot/etc/os-release" ]]; then
  sed -i \
    -e 's/^NAME=.*/NAME="VNOS"/' \
    -e 's/^PRETTY_NAME=.*/PRETTY_NAME="VNOS 24.04.3 LTS"/' \
    -e 's/^ID=.*/ID=vnos/' \
    "$WORKDIR/chroot/etc/os-release" || true
fi
if [[ -f "$WORKDIR/chroot/usr/lib/os-release" ]]; then
  sed -i \
    -e 's/^NAME=.*/NAME="VNOS"/' \
    -e 's/^PRETTY_NAME=.*/PRETTY_NAME="VNOS 24.04.3 LTS"/' \
    -e 's/^ID=.*/ID=vnos/' \
    "$WORKDIR/chroot/usr/lib/os-release" || true
fi
if [[ -f "$WORKDIR/chroot/etc/lsb-release" ]]; then
  sed -i \
    -e 's/^DISTRIB_ID=.*/DISTRIB_ID=VNOS/' \
    -e 's/^DISTRIB_DESCRIPTION=.*/DISTRIB_DESCRIPTION="VNOS 24.04.3 LTS"/' \
    "$WORKDIR/chroot/etc/lsb-release" || true
fi
if [[ -f "$WORKDIR/chroot/etc/default/grub" ]]; then
  sed -i \
    -e 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="plymouth.enable=0 nosplash loglevel=4 systemd.show_status=1"/' \
    "$WORKDIR/chroot/etc/default/grub" || true
fi

# Replace common distro logos
VNOS_LOGO="$WORKDIR/chroot/usr/local/share/vnde/vnde/icons/scalable/apps/vnde-menu.svg"
if [[ -f "$VNOS_LOGO" ]]; then
  mkdir -p "$WORKDIR/chroot/usr/share/pixmaps"
  cp "$VNOS_LOGO" "$WORKDIR/chroot/usr/share/pixmaps/vnos-logo.svg"
  for f in \
    "$WORKDIR/chroot/usr/share/icons/Yaru/scalable/places/distributor-logo.svg" \
    "$WORKDIR/chroot/usr/share/icons/hicolor/scalable/apps/distributor-logo.svg" \
    "$WORKDIR/chroot/usr/share/icons/hicolor/scalable/apps/ubuntu-logo-icon.svg" \
    "$WORKDIR/chroot/usr/share/pixmaps/distributor-logo.svg" \
    "$WORKDIR/chroot/usr/share/pixmaps/ubuntu-logo-icon.svg"; do
    if [[ -f "$f" ]]; then
      cp "$VNOS_LOGO" "$f"
    fi
  done
  while IFS= read -r f; do
    cp "$VNOS_LOGO" "$f"
  done < <(find "$WORKDIR/chroot/usr/share/icons" -type f \( -name '*ubuntu*logo*.svg' -o -name 'distributor-logo*.svg' \) 2>/dev/null || true)
fi

echo "[INFO] Cai dat splash VNOS (Plymouth)..."
mkdir -p "$WORKDIR/chroot/usr/share/plymouth/themes/vnos"
if [[ -f "$WORKDIR/chroot/usr/local/share/vnde/assets/wallpapers/vietnam-dawn-demo.png" ]]; then
  cp "$WORKDIR/chroot/usr/local/share/vnde/assets/wallpapers/vietnam-dawn-demo.png" \
    "$WORKDIR/chroot/usr/share/plymouth/themes/vnos/vnos.png"
else
  # Fallback image if project wallpaper is missing.
  cp "$WORKDIR/chroot/usr/local/share/vnde/vnde/icons/scalable/apps/vnde-menu.svg" \
    "$WORKDIR/chroot/usr/share/plymouth/themes/vnos/vnos.png" 2>/dev/null || true
fi
cat > "$WORKDIR/chroot/usr/share/plymouth/themes/vnos/vnos.plymouth" <<'EOF'
[Plymouth Theme]
Name=VNOS Splash
Description=VNOS branded boot splash
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/vnos
ScriptFile=/usr/share/plymouth/themes/vnos/vnos.script
EOF
cat > "$WORKDIR/chroot/usr/share/plymouth/themes/vnos/vnos.script" <<'EOF'
screen_w = Window.GetWidth();
screen_h = Window.GetHeight();
img = Image("vnos.png");
sprite = Sprite(img);
sprite.SetX((screen_w - img.GetWidth()) / 2);
sprite.SetY((screen_h - img.GetHeight()) / 2);
EOF
mkdir -p "$WORKDIR/chroot/etc/plymouth"
cat > "$WORKDIR/chroot/etc/plymouth/plymouthd.conf" <<'EOF'
[Daemon]
Theme=vnos
ShowDelay=0
DeviceTimeout=8
EOF
if [[ -d "$WORKDIR/chroot/etc/alternatives" ]]; then
  ln -sf /usr/share/plymouth/themes/vnos/vnos.plymouth \
    "$WORKDIR/chroot/etc/alternatives/default.plymouth" || true
fi

echo "[INFO] Patch base layer minimal.squashfs (boot splash)..."
BASE_SQFS="$WORKDIR/iso/casper/minimal.squashfs"
if [[ -f "$BASE_SQFS" && "$BASE_SQFS" != "$SQFS" ]]; then
  rm -rf "$WORKDIR/basechroot"
  mkdir -p "$WORKDIR/basechroot"
  unsquashfs -f -d "$WORKDIR/basechroot" "$BASE_SQFS" >/dev/null

  replace_text_tree "$WORKDIR/basechroot/etc"
  replace_text_tree "$WORKDIR/basechroot/usr/share"

  if [[ -f "$WORKDIR/basechroot/etc/os-release" ]]; then
    sed -i \
      -e 's/^NAME=.*/NAME="VNOS"/' \
      -e 's/^PRETTY_NAME=.*/PRETTY_NAME="VNOS 24.04.3 LTS"/' \
      -e 's/^ID=.*/ID=vnos/' \
      "$WORKDIR/basechroot/etc/os-release" || true
  fi
  if [[ -f "$WORKDIR/basechroot/usr/lib/os-release" ]]; then
    sed -i \
      -e 's/^NAME=.*/NAME="VNOS"/' \
      -e 's/^PRETTY_NAME=.*/PRETTY_NAME="VNOS 24.04.3 LTS"/' \
      -e 's/^ID=.*/ID=vnos/' \
      "$WORKDIR/basechroot/usr/lib/os-release" || true
  fi
  if [[ -f "$WORKDIR/basechroot/etc/lsb-release" ]]; then
    sed -i \
      -e 's/^DISTRIB_ID=.*/DISTRIB_ID=VNOS/' \
      -e 's/^DISTRIB_DESCRIPTION=.*/DISTRIB_DESCRIPTION="VNOS 24.04.3 LTS"/' \
      "$WORKDIR/basechroot/etc/lsb-release" || true
  fi
  if [[ -f "$WORKDIR/basechroot/etc/default/grub" ]]; then
    sed -i \
      -e 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="plymouth.enable=0 nosplash loglevel=4 systemd.show_status=1"/' \
      "$WORKDIR/basechroot/etc/default/grub" || true
  fi

  BASE_LOGO_SVG="$ROOT_DIR/vnde/icons/scalable/apps/vnde-menu.svg"
  if [[ -f "$BASE_LOGO_SVG" ]]; then
    mkdir -p "$WORKDIR/basechroot/usr/share/pixmaps"
    cp "$BASE_LOGO_SVG" "$WORKDIR/basechroot/usr/share/pixmaps/vnos-logo.svg"
    while IFS= read -r f; do
      cp "$BASE_LOGO_SVG" "$f"
    done < <(find "$WORKDIR/basechroot/usr/share/icons" "$WORKDIR/basechroot/usr/share/pixmaps" -type f \( -name '*ubuntu*logo*.svg' -o -name 'distributor-logo*.svg' \) 2>/dev/null || true)
  fi

  mkdir -p "$WORKDIR/basechroot/usr/share/plymouth/themes/vnos"
  if [[ -f "$ROOT_DIR/assets/wallpapers/vietnam-dawn-demo.png" ]]; then
    cp "$ROOT_DIR/assets/wallpapers/vietnam-dawn-demo.png" \
      "$WORKDIR/basechroot/usr/share/plymouth/themes/vnos/vnos.png"
  fi
  cat > "$WORKDIR/basechroot/usr/share/plymouth/themes/vnos/vnos.plymouth" <<'EOF'
[Plymouth Theme]
Name=VNOS Splash
Description=VNOS branded boot splash
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/vnos
ScriptFile=/usr/share/plymouth/themes/vnos/vnos.script
EOF
  cat > "$WORKDIR/basechroot/usr/share/plymouth/themes/vnos/vnos.script" <<'EOF'
screen_w = Window.GetWidth();
screen_h = Window.GetHeight();
img = Image("vnos.png");
sprite = Sprite(img);
sprite.SetX((screen_w - img.GetWidth()) / 2);
sprite.SetY((screen_h - img.GetHeight()) / 2);
EOF
  mkdir -p "$WORKDIR/basechroot/etc/plymouth" "$WORKDIR/basechroot/etc/alternatives"
  cat > "$WORKDIR/basechroot/etc/plymouth/plymouthd.conf" <<'EOF'
[Daemon]
Theme=vnos
ShowDelay=0
DeviceTimeout=8
EOF
  ln -sf /usr/share/plymouth/themes/vnos/vnos.plymouth \
    "$WORKDIR/basechroot/etc/alternatives/default.plymouth" || true

  rm -f "$BASE_SQFS"
  mksquashfs "$WORKDIR/basechroot" "$BASE_SQFS" -comp xz -noappend >/dev/null
  if [[ -f "${BASE_SQFS%.squashfs}.size" ]]; then
    printf "%s" "$(du -sx --block-size=1 "$WORKDIR/basechroot" | awk '{print $1}')" > "${BASE_SQFS%.squashfs}.size"
  fi
fi

echo "[INFO] Tao wrapper lenh vnde..."
mkdir -p "$WORKDIR/chroot/usr/local/bin"
cat > "$WORKDIR/chroot/usr/local/bin/vnde" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
export VNDE_SOURCE_DIR="/usr/local/share/vnde"
exec /usr/local/share/vnde/vnde/scripts/vnde "$@"
SH
chmod +x "$WORKDIR/chroot/usr/local/bin/vnde"

for s in vnde-install vnde-update vnde-bootstrap; do
  cat > "$WORKDIR/chroot/usr/local/bin/$s" <<SH
#!/usr/bin/env bash
set -euo pipefail
exec /usr/local/bin/vnde ${s#vnde-} "\$@"
SH
  chmod +x "$WORKDIR/chroot/usr/local/bin/$s"
done

echo "[INFO] Them auto-setup VNDE lan dau dang nhap..."
mkdir -p "$WORKDIR/chroot/usr/local/bin" "$WORKDIR/chroot/etc/skel/.config/autostart"
cat > "$WORKDIR/chroot/usr/local/bin/vnde-first-login" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
MARK="$HOME/.config/vnde/.first_login_done"
mkdir -p "$HOME/.config/vnde" "$HOME/.cache"
if [[ -f "$MARK" ]]; then
  exit 0
fi
nohup /usr/local/bin/vnde install --profile gnome --no-packages >"$HOME/.cache/vnde-first-login.log" 2>&1 &
touch "$MARK"
SH
chmod +x "$WORKDIR/chroot/usr/local/bin/vnde-first-login"

cat > "$WORKDIR/chroot/etc/skel/.config/autostart/vnde-first-login.desktop" <<'DESK'
[Desktop Entry]
Type=Application
Name=VNDE First Login Setup
Exec=/usr/local/bin/vnde-first-login
X-GNOME-Autostart-enabled=true
NoDisplay=true
DESK

echo "[INFO] Unmount chroot helpers truoc khi dong goi..."
if mountpoint -q "$WORKDIR/chroot/dev"; then umount -lf "$WORKDIR/chroot/dev"; fi
if mountpoint -q "$WORKDIR/chroot/proc"; then umount -lf "$WORKDIR/chroot/proc"; fi
if mountpoint -q "$WORKDIR/chroot/sys"; then umount -lf "$WORKDIR/chroot/sys"; fi

echo "[INFO] Rebuild $(basename "$SQFS")..."
rm -f "$SQFS"
mksquashfs "$WORKDIR/chroot" "$SQFS" -comp xz -noappend >/dev/null

echo "[INFO] Update size metadata..."
ROOTFS_SIZE="$(du -sx --block-size=1 "$WORKDIR/chroot" | awk '{print $1}')"
if [[ -f "$WORKDIR/iso/casper/filesystem.size" ]]; then
  printf "%s" "$ROOTFS_SIZE" > "$WORKDIR/iso/casper/filesystem.size"
fi
SQFS_SIZE_FILE="${SQFS%.squashfs}.size"
if [[ -f "$SQFS_SIZE_FILE" ]]; then
  printf "%s" "$ROOTFS_SIZE" > "$SQFS_SIZE_FILE"
fi

echo "[INFO] Rebuild ISO..."
rm -f "$ISO_OUT"
xorriso -as mkisofs \
  -r -V "VNOS_24_04_3" \
  -o "$ISO_OUT" \
  -J -l \
  -b boot/grub/i386-pc/eltorito.img \
  -c boot.catalog \
  -no-emul-boot -boot-load-size 4 -boot-info-table \
  -eltorito-alt-boot \
  -e EFI/boot/grubx64.efi \
  -no-emul-boot \
  "$WORKDIR/iso" >/dev/null

echo "[OK  ] Tao xong ISO: $ISO_OUT"
echo "[NOTE] Neu ISO khong boot tren 1 so may UEFI, dung Cubic hoac remastersys de dong goi lai boot metadata."
