#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WALLPAPER_SRC="$ROOT_DIR/assets/wallpapers/vietnam-dawn.svg"
TARGET_WALLPAPER="$HOME/.local/share/backgrounds/vietnam-dawn.svg"
DRY_RUN=0
INSTALL_PACKAGES=1
WALLPAPER_ONLY=0

log() { printf '[INFO] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*"; }
err() { printf '[ERR ] %s\n' "$*"; }

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY ] %s\n' "$*"
  else
    eval "$@"
  fi
}

usage() {
  cat <<USAGE
Vietnam Style Desktop Installer

Usage:
  ./install.sh [options]

Options:
  --dry-run         Show commands without applying changes
  --no-packages     Skip package installation
  --wallpaper-only  Only install and apply wallpaper
  -h, --help        Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --no-packages)
      INSTALL_PACKAGES=0
      ;;
    --wallpaper-only)
      WALLPAPER_ONLY=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      err "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

if [[ ! -f "$WALLPAPER_SRC" ]]; then
  err "Wallpaper source not found: $WALLPAPER_SRC"
  exit 1
fi

get_pm() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "apt"
  elif command -v dnf >/dev/null 2>&1; then
    echo "dnf"
  elif command -v pacman >/dev/null 2>&1; then
    echo "pacman"
  elif command -v zypper >/dev/null 2>&1; then
    echo "zypper"
  else
    echo "unknown"
  fi
}

install_common_packages() {
  local pm="$1"
  case "$pm" in
    apt)
      run_cmd "sudo apt-get update"
      run_cmd "sudo apt-get install -y fonts-noto-color-emoji fonts-noto-core papirus-icon-theme gnome-tweaks"
      ;;
    dnf)
      run_cmd "sudo dnf install -y google-noto-fonts papirus-icon-theme gnome-tweaks"
      ;;
    pacman)
      run_cmd "sudo pacman -Sy --noconfirm noto-fonts papirus-icon-theme gnome-tweaks"
      ;;
    zypper)
      run_cmd "sudo zypper install -y google-noto-fonts papirus-icon-theme gnome-tweaks"
      ;;
    *)
      warn "Unsupported package manager. Skipping package installation."
      ;;
  esac
}

detect_de() {
  local de="${XDG_CURRENT_DESKTOP:-}"
  de="${de,,}"

  if [[ "$de" == *"gnome"* ]]; then
    echo "gnome"
  elif [[ "$de" == *"kde"* || "$de" == *"plasma"* ]]; then
    echo "kde"
  elif [[ "$de" == *"xfce"* ]]; then
    echo "xfce"
  else
    echo "unknown"
  fi
}

install_wallpaper() {
  run_cmd "mkdir -p \"$HOME/.local/share/backgrounds\""
  run_cmd "cp \"$WALLPAPER_SRC\" \"$TARGET_WALLPAPER\""
  log "Wallpaper installed: $TARGET_WALLPAPER"
}

apply_gnome() {
  if ! command -v gsettings >/dev/null 2>&1; then
    warn "gsettings not found. GNOME settings skipped."
    return
  fi

  run_cmd "gsettings set org.gnome.desktop.background picture-uri \"file://$TARGET_WALLPAPER\""
  run_cmd "gsettings set org.gnome.desktop.background picture-uri-dark \"file://$TARGET_WALLPAPER\""

  if [[ "$WALLPAPER_ONLY" -eq 0 ]]; then
    run_cmd "gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita'"
    run_cmd "gsettings set org.gnome.desktop.interface icon-theme 'Papirus'"
    run_cmd "gsettings set org.gnome.desktop.interface font-name 'Noto Sans 11'"
    run_cmd "gsettings set org.gnome.desktop.interface monospace-font-name 'Noto Sans Mono 11'"
    run_cmd "gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'"
  fi

  log "Applied GNOME settings."
}

apply_kde() {
  if command -v plasma-apply-wallpaperimage >/dev/null 2>&1; then
    run_cmd "plasma-apply-wallpaperimage \"$TARGET_WALLPAPER\""
    log "Applied KDE wallpaper using plasma-apply-wallpaperimage."
  elif command -v qdbus >/dev/null 2>&1 || command -v qdbus6 >/dev/null 2>&1; then
    warn "KDE wallpaper helper exists but scripted DBus flow is distro-specific. Set wallpaper manually if needed."
  else
    warn "No KDE wallpaper tool found."
  fi

  if [[ "$WALLPAPER_ONLY" -eq 0 ]]; then
    warn "KDE theme/font automation is intentionally minimal to avoid breaking existing global themes."
  fi
}

apply_xfce() {
  if ! command -v xfconf-query >/dev/null 2>&1; then
    warn "xfconf-query not found. XFCE settings skipped."
    return
  fi

  local channel="xfce4-desktop"
  local props
  props=$(xfconf-query -c "$channel" -l | grep "last-image" || true)

  if [[ -z "$props" ]]; then
    warn "Could not find XFCE wallpaper properties automatically."
    return
  fi

  while IFS= read -r prop; do
    [[ -z "$prop" ]] && continue
    run_cmd "xfconf-query -c \"$channel\" -p \"$prop\" -s \"$TARGET_WALLPAPER\""
  done <<< "$props"

  log "Applied XFCE wallpaper across detected screens/workspaces."
}

install_terminal_themes() {
  if [[ "$WALLPAPER_ONLY" -eq 1 ]]; then
    return
  fi

  if [[ -d "$HOME/.config/kitty" ]]; then
    run_cmd "mkdir -p \"$HOME/.config/kitty/themes\""
    run_cmd "cp \"$ROOT_DIR/themes/kitty/vietnam.conf\" \"$HOME/.config/kitty/themes/vietnam.conf\""
    if ! grep -q "themes/vietnam.conf" "$HOME/.config/kitty/kitty.conf" 2>/dev/null; then
      run_cmd "printf '\ninclude themes/vietnam.conf\n' >> \"$HOME/.config/kitty/kitty.conf\""
    fi
    log "Kitty theme installed."
  fi

  if [[ -f "$HOME/.config/alacritty/alacritty.toml" ]]; then
    run_cmd "mkdir -p \"$HOME/.config/alacritty/themes\""
    run_cmd "cp \"$ROOT_DIR/themes/alacritty/vietnam.toml\" \"$HOME/.config/alacritty/themes/vietnam.toml\""
    if ! grep -q "themes/vietnam.toml" "$HOME/.config/alacritty/alacritty.toml" 2>/dev/null; then
      run_cmd "printf '\nimport = [\"~/.config/alacritty/themes/vietnam.toml\"]\n' >> \"$HOME/.config/alacritty/alacritty.toml\""
    fi
    log "Alacritty theme installed."
  fi
}

main() {
  log "Starting Vietnam style desktop setup"

  install_wallpaper

  if [[ "$INSTALL_PACKAGES" -eq 1 && "$WALLPAPER_ONLY" -eq 0 ]]; then
    local pm
    pm="$(get_pm)"
    log "Detected package manager: $pm"
    install_common_packages "$pm"
  fi

  local de
  de="$(detect_de)"
  log "Detected desktop environment: $de"

  case "$de" in
    gnome)
      apply_gnome
      ;;
    kde)
      apply_kde
      ;;
    xfce)
      apply_xfce
      ;;
    *)
      warn "Unsupported/unknown DE. Wallpaper installed only."
      ;;
  esac

  install_terminal_themes

  log "Done. You may need to re-login for all font/icon changes to fully apply."
}

main
