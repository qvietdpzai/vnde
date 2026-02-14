#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=0
NO_PACKAGES=0
PROFILE="gnome"

log() { printf '[INFO] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*"; }
err() { printf '[ERR ] %s\n' "$*"; }

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY ] %s\n' "$*"
  else
    eval "$*"
  fi
}

usage() {
  cat <<USAGE
VNDE Installer

Usage:
  ./install-vnde.sh [options]

Options:
  --profile gnome|kde       Install profile type (default: gnome)
  --dry-run                 Show commands only
  --no-packages             Skip package installation
  -h, --help                Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="${2:-}"; shift ;;
    --dry-run) DRY_RUN=1 ;;
    --no-packages) NO_PACKAGES=1 ;;
    -h|--help) usage; exit 0 ;;
    *) err "Unknown option: $1"; usage; exit 1 ;;
  esac
  shift
done

if [[ "$PROFILE" != "gnome" && "$PROFILE" != "kde" ]]; then
  err "Invalid --profile: $PROFILE"
  exit 1
fi

get_pm() {
  if command -v apt-get >/dev/null 2>&1; then
    echo apt
  elif command -v dnf >/dev/null 2>&1; then
    echo dnf
  elif command -v pacman >/dev/null 2>&1; then
    echo pacman
  elif command -v zypper >/dev/null 2>&1; then
    echo zypper
  else
    echo unknown
  fi
}

install_packages_gnome() {
  local pm="$1"
  case "$pm" in
    apt)
      run_cmd "sudo apt-get update"
      run_cmd "sudo apt-get install -y gnome-shell gnome-session gnome-shell-extensions gnome-tweaks gnome-shell-extension-manager gnome-software gnome-software-plugin-flatpak gnome-software-plugin-snap rofi flameshot ibus ibus-unikey fonts-noto-core fonts-noto-color-emoji papirus-icon-theme xdg-utils flatpak snapd docker.io docker-compose-v2 python3-gi python3-feedparser gir1.2-gtk-4.0 libnotify-bin xclip xdotool"
      ;;
    dnf)
      run_cmd "sudo dnf install -y gnome-shell gnome-session gnome-extensions-app gnome-tweaks gnome-software gnome-software-plugin-flatpak rofi flameshot ibus ibus-bamboo google-noto-sans-fonts google-noto-emoji-fonts papirus-icon-theme xdg-utils flatpak docker docker-compose python3-gobject python3-feedparser gtk4 libnotify xclip xdotool"
      ;;
    pacman)
      run_cmd "sudo pacman -Sy --noconfirm gnome-shell gnome-session gnome-shell-extensions gnome-tweaks gnome-software rofi flameshot ibus ibus-unikey noto-fonts noto-fonts-emoji papirus-icon-theme xdg-utils flatpak snapd docker docker-compose python-gobject python-feedparser gtk4 libnotify xclip xdotool"
      ;;
    zypper)
      run_cmd "sudo zypper install -y gnome-shell gnome-session gnome-shell-extensions gnome-tweaks gnome-software gnome-software-plugin-flatpak rofi flameshot ibus-unikey google-noto-fonts papirus-icon-theme xdg-utils flatpak snapd docker docker-compose python3-gobject python3-feedparser gtk4-tools libnotify-tools xclip xdotool"
      ;;
    *)
      warn "Unsupported package manager. Install dependencies manually."
      ;;
  esac
}

install_packages_kde() {
  local pm="$1"
  case "$pm" in
    apt)
      run_cmd "sudo apt-get update"
      run_cmd "sudo apt-get install -y plasma-desktop plasma-workspace kde-config-gtk-style dolphin konsole sddm-theme-breeze rofi flameshot ibus ibus-unikey fonts-noto-core fonts-noto-color-emoji papirus-icon-theme xdg-utils flatpak snapd docker.io docker-compose-v2 python3-gi python3-feedparser gir1.2-gtk-4.0 libnotify-bin xclip xdotool"
      ;;
    dnf)
      run_cmd "sudo dnf install -y @kde-desktop-environment dolphin konsole rofi flameshot ibus ibus-bamboo google-noto-sans-fonts google-noto-emoji-fonts papirus-icon-theme xdg-utils flatpak docker docker-compose python3-gobject python3-feedparser gtk4 libnotify xclip xdotool"
      ;;
    pacman)
      run_cmd "sudo pacman -Sy --noconfirm plasma-desktop plasma-workspace dolphin konsole rofi flameshot ibus ibus-unikey noto-fonts noto-fonts-emoji papirus-icon-theme xdg-utils flatpak snapd docker docker-compose python-gobject python-feedparser gtk4 libnotify xclip xdotool"
      ;;
    zypper)
      run_cmd "sudo zypper install -y patterns-kde-kde kde-cli-tools5 dolphin konsole rofi flameshot ibus-unikey google-noto-fonts papirus-icon-theme xdg-utils flatpak snapd docker docker-compose python3-gobject python3-feedparser gtk4-tools libnotify-tools xclip xdotool"
      ;;
    *)
      warn "Unsupported package manager. Install KDE dependencies manually."
      ;;
  esac
}

setup_services() {
  if command -v systemctl >/dev/null 2>&1; then
    run_cmd "sudo systemctl enable --now snapd.socket || true"
    run_cmd "sudo systemctl enable --now docker || true"
  fi
  if getent group docker >/dev/null 2>&1; then
    run_cmd "sudo usermod -aG docker \"$USER\" || true"
  fi
  if command -v flatpak >/dev/null 2>&1; then
    run_cmd "sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo"
  fi
}

install_shared_files() {
  local SOURCE_MIRROR="$HOME/.local/share/vnde/source"
  run_cmd "mkdir -p \"$HOME/.config/vnde/rofi\" \"$HOME/.local/bin\" \"$HOME/.local/share/applications\" \"$HOME/.local/share/icons/hicolor/scalable/apps\" \"$HOME/.local/share/backgrounds\" \"$HOME/.local/share/vnde/gui\" \"$HOME/.local/share/vnde/source\" \"$HOME/.config/autostart\""

  # Keep a local source copy so users can run vnde-install / vnde-update from terminal.
  if [[ "$(realpath "$ROOT_DIR" 2>/dev/null || echo "$ROOT_DIR")" != "$(realpath "$SOURCE_MIRROR" 2>/dev/null || echo "$SOURCE_MIRROR")" ]]; then
    run_cmd "cp -a \"$ROOT_DIR/.\" \"$SOURCE_MIRROR/\""
  else
    log "Source mirror is current directory; skip source copy."
  fi

  run_cmd "cp \"$ROOT_DIR/vnde/rofi/vnde.rasi\" \"$HOME/.config/vnde/rofi/vnde.rasi\""
  run_cmd "cp \"$ROOT_DIR/vnde/rofi/vn-terminal-menu.rasi\" \"$HOME/.config/vnde/rofi/vn-terminal-menu.rasi\""
  run_cmd "cp \"$ROOT_DIR/assets/wallpapers/vietnam-dawn.svg\" \"$HOME/.local/share/backgrounds/vietnam-dawn.svg\""

  run_cmd "cp \"$ROOT_DIR/vnde/gui/vn_app_center.py\" \"$HOME/.local/share/vnde/gui/vn_app_center.py\""
  run_cmd "cp \"$ROOT_DIR/vnde/gui/vn_news_center.py\" \"$HOME/.local/share/vnde/gui/vn_news_center.py\""
  run_cmd "cp \"$ROOT_DIR/vnde/gui/vn_music_center.py\" \"$HOME/.local/share/vnde/gui/vn_music_center.py\""
  run_cmd "cp \"$ROOT_DIR/vnde/gui/vn_menu_center.py\" \"$HOME/.local/share/vnde/gui/vn_menu_center.py\""
  run_cmd "cp \"$ROOT_DIR/vnde/gui/vn_file_manager.py\" \"$HOME/.local/share/vnde/gui/vn_file_manager.py\""

  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vn-app-store\" \"$HOME/.local/bin/vn-app-store\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vn-news\" \"$HOME/.local/bin/vn-news\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vn-music\" \"$HOME/.local/bin/vn-music\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vn-menu\" \"$HOME/.local/bin/vn-menu\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vn-terminal\" \"$HOME/.local/bin/vn-terminal\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vn-terminal-context-menu\" \"$HOME/.local/bin/vn-terminal-context-menu\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/menu\" \"$HOME/.local/bin/menu\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vn-file-manager\" \"$HOME/.local/bin/vn-file-manager\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vn-sound-popup\" \"$HOME/.local/bin/vn-sound-popup\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vn-news-cli\" \"$HOME/.local/bin/vn-news-cli\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vn-news-panel\" \"$HOME/.local/bin/vn-news-panel\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vnkde-startup-splash\" \"$HOME/.local/bin/vnkde-startup-splash\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vnde-install\" \"$HOME/.local/bin/vnde-install\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vnde-update\" \"$HOME/.local/bin/vnde-update\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vnde\" \"$HOME/.local/bin/vnde\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/bootstrap-vnde.sh\" \"$HOME/.local/bin/vnde-bootstrap\""

  run_cmd "chmod +x \"$HOME/.local/share/vnde/gui/vn_app_center.py\" \"$HOME/.local/share/vnde/gui/vn_news_center.py\" \"$HOME/.local/share/vnde/gui/vn_music_center.py\" \"$HOME/.local/share/vnde/gui/vn_menu_center.py\" \"$HOME/.local/share/vnde/gui/vn_file_manager.py\""
  run_cmd "chmod +x \"$HOME/.local/bin/vn-app-store\" \"$HOME/.local/bin/vn-news\" \"$HOME/.local/bin/vn-music\" \"$HOME/.local/bin/vn-menu\" \"$HOME/.local/bin/vn-terminal\" \"$HOME/.local/bin/vn-terminal-context-menu\" \"$HOME/.local/bin/menu\" \"$HOME/.local/bin/vn-file-manager\" \"$HOME/.local/bin/vn-sound-popup\" \"$HOME/.local/bin/vn-news-cli\" \"$HOME/.local/bin/vn-news-panel\" \"$HOME/.local/bin/vnkde-startup-splash\" \"$HOME/.local/bin/vnde-install\" \"$HOME/.local/bin/vnde-update\" \"$HOME/.local/bin/vnde\" \"$HOME/.local/bin/vnde-bootstrap\""
  run_cmd "sudo install -Dm755 \"$HOME/.local/bin/vnde-install\" /usr/local/bin/vnde-install || true"
  run_cmd "sudo install -Dm755 \"$HOME/.local/bin/vnde-update\" /usr/local/bin/vnde-update || true"
  run_cmd "sudo install -Dm755 \"$HOME/.local/bin/vnde\" /usr/local/bin/vnde || true"
  run_cmd "sudo install -Dm755 \"$HOME/.local/bin/vnde-bootstrap\" /usr/local/bin/vnde-bootstrap || true"

  run_cmd "cp \"$ROOT_DIR/vnde/applications/vnde-app-store.desktop\" \"$HOME/.local/share/applications/vnde-app-store.desktop\""
  run_cmd "cp \"$ROOT_DIR/vnde/applications/vnde-news.desktop\" \"$HOME/.local/share/applications/vnde-news.desktop\""
  run_cmd "cp \"$ROOT_DIR/vnde/applications/vnde-news-cli.desktop\" \"$HOME/.local/share/applications/vnde-news-cli.desktop\""
  run_cmd "cp \"$ROOT_DIR/vnde/applications/vnde-music.desktop\" \"$HOME/.local/share/applications/vnde-music.desktop\""
  run_cmd "cp \"$ROOT_DIR/vnde/applications/vnde-menu.desktop\" \"$HOME/.local/share/applications/vnde-menu.desktop\""
  run_cmd "cp \"$ROOT_DIR/vnde/applications/vnde-terminal.desktop\" \"$HOME/.local/share/applications/vnde-terminal.desktop\""
  run_cmd "cp \"$ROOT_DIR/vnde/applications/vnde-file-manager.desktop\" \"$HOME/.local/share/applications/vnde-file-manager.desktop\""
  run_cmd "cp \"$ROOT_DIR/vnde/applications/vnde-docker.desktop\" \"$HOME/.local/share/applications/vnde-docker.desktop\""

  run_cmd "cp \"$ROOT_DIR/vnde/autostart/vn-news-panel.desktop\" \"$HOME/.config/autostart/vn-news-panel.desktop\""
  run_cmd "cp \"$ROOT_DIR/vnde/autostart/vnkde-splash.desktop\" \"$HOME/.config/autostart/vnkde-splash.desktop\""

  run_cmd "cp \"$ROOT_DIR/vnde/icons/scalable/apps/vnde-app-store.svg\" \"$HOME/.local/share/icons/hicolor/scalable/apps/vnde-app-store.svg\""
  run_cmd "cp \"$ROOT_DIR/vnde/icons/scalable/apps/vnde-news.svg\" \"$HOME/.local/share/icons/hicolor/scalable/apps/vnde-news.svg\""
  run_cmd "cp \"$ROOT_DIR/vnde/icons/scalable/apps/vnde-music.svg\" \"$HOME/.local/share/icons/hicolor/scalable/apps/vnde-music.svg\""
  run_cmd "cp \"$ROOT_DIR/vnde/icons/scalable/apps/vnde-menu.svg\" \"$HOME/.local/share/icons/hicolor/scalable/apps/vnde-menu.svg\""
  run_cmd "cp \"$ROOT_DIR/vnde/icons/scalable/apps/vnde-terminal.svg\" \"$HOME/.local/share/icons/hicolor/scalable/apps/vnde-terminal.svg\""
  run_cmd "cp \"$ROOT_DIR/vnde/icons/scalable/apps/vnde-file-manager.svg\" \"$HOME/.local/share/icons/hicolor/scalable/apps/vnde-file-manager.svg\""
  run_cmd "cp \"$ROOT_DIR/vnde/icons/scalable/apps/vnde-docker.svg\" \"$HOME/.local/share/icons/hicolor/scalable/apps/vnde-docker.svg\""

  run_cmd "update-desktop-database \"$HOME/.local/share/applications\" >/dev/null 2>&1 || true"
  run_cmd "gtk-update-icon-cache -q \"$HOME/.local/share/icons/hicolor\" >/dev/null 2>&1 || true"
}

configure_locale() {
  run_cmd "mkdir -p \"$HOME/.config/environment.d\""
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY ] write %s\n' "$HOME/.config/environment.d/90-vnde.conf"
    return
  fi
  cat > "$HOME/.config/environment.d/90-vnde.conf" <<ENV
LANG=vi_VN.UTF-8
LANGUAGE=vi_VN:vi
LC_TIME=vi_VN.UTF-8
XMODIFIERS=@im=ibus
GTK_IM_MODULE=ibus
QT_IM_MODULE=ibus
ENV
}

set_gnome_keybinding() {
  local path="$1"; local name="$2"; local cmd="$3"; local binding="$4"
  run_cmd "gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${path} name '$name'"
  run_cmd "gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${path} command '$cmd'"
  run_cmd "gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${path} binding '$binding'"
}

install_vnde_gnome_session() {
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vnde-gnome-session\" \"$HOME/.local/bin/vnde-gnome-session\""
  run_cmd "chmod +x \"$HOME/.local/bin/vnde-gnome-session\""

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY ] write %s\n' "$HOME/.local/share/xsessions/vnde.desktop"
    printf '[DRY ] install %s\n' "/usr/share/xsessions/vnde.desktop"
    return
  fi

  mkdir -p "$HOME/.local/share/xsessions"
  cat > "$HOME/.local/share/xsessions/vnde.desktop" <<DESKTOP
[Desktop Entry]
Name=VNDE
Comment=Vietnam Desktop Experience on GNOME Shell
Exec=$HOME/.local/bin/vnde-gnome-session
TryExec=gnome-shell
Type=Application
DesktopNames=GNOME;VNDE
DESKTOP

  tmp="$HOME/.cache/vnde.desktop"
  mkdir -p "$HOME/.cache"
  cp "$HOME/.local/share/xsessions/vnde.desktop" "$tmp"
  run_cmd "sudo install -Dm644 \"$tmp\" /usr/share/xsessions/vnde.desktop || true"
}

install_vnde_kde_session() {
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vnde-kde-session\" \"$HOME/.local/bin/vnde-kde-session\""
  run_cmd "chmod +x \"$HOME/.local/bin/vnde-kde-session\""

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY ] write %s\n' "$HOME/.local/share/xsessions/vnde-kde.desktop"
    printf '[DRY ] install %s\n' "/usr/share/xsessions/vnde-kde.desktop"
    return
  fi

  mkdir -p "$HOME/.local/share/xsessions"
  cat > "$HOME/.local/share/xsessions/vnde-kde.desktop" <<DESKTOP
[Desktop Entry]
Name=VNDE (KDE)
Comment=Vietnam Desktop Experience on KDE Plasma
Exec=$HOME/.local/bin/vnde-kde-session
TryExec=startplasma-x11
Type=Application
DesktopNames=KDE;VNDE
DESKTOP

  tmp="$HOME/.cache/vnde-kde.desktop"
  mkdir -p "$HOME/.cache"
  cp "$HOME/.local/share/xsessions/vnde-kde.desktop" "$tmp"
  run_cmd "sudo install -Dm644 \"$tmp\" /usr/share/xsessions/vnde-kde.desktop || true"
}

configure_kde() {
  local wp="$HOME/.local/share/backgrounds/vietnam-dawn.svg"
  local appletrc="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
  local ksplashrc="$HOME/.config/ksplashrc"
  local kwrite=""
  local pairs=""

  if command -v plasma-apply-wallpaperimage >/dev/null 2>&1; then
    run_cmd "plasma-apply-wallpaperimage \"$wp\" || true"
  fi

  if command -v kwriteconfig6 >/dev/null 2>&1; then
    kwrite="kwriteconfig6"
  elif command -v kwriteconfig5 >/dev/null 2>&1; then
    kwrite="kwriteconfig5"
  fi

  # Disable default KDE splash ("Made by KDE") and use VNDE splash autostart.
  if [[ -n "$kwrite" ]]; then
    run_cmd "$kwrite --file \"$ksplashrc\" --group KSplash --key Theme None"
    run_cmd "$kwrite --file \"$ksplashrc\" --group KSplash --key Engine none"
  else
    warn "kwriteconfig not found. Cannot disable default KDE splash automatically."
  fi

  if [[ -z "$kwrite" || ! -f "$appletrc" ]]; then
    warn "KDE launcher branding skipped (plasma appletrc unavailable)."
    log "KDE profile applied."
    return
  fi

  pairs="$(python3 - "$appletrc" <<'PY'
import re
import sys

path = sys.argv[1]
targets = {"org.kde.plasma.kickoff", "org.kde.plasma.kicker", "org.kde.plasma.kickerdash"}
current = None
found = []

for raw in open(path, "r", encoding="utf-8", errors="ignore"):
    line = raw.strip()
    m = re.match(r"^\[Containments\]\[(\d+)\]\[Applets\]\[(\d+)\]$", line)
    if m:
        current = (m.group(1), m.group(2))
        continue
    if current and line.startswith("plugin="):
        plugin = line.split("=", 1)[1].strip()
        if plugin in targets:
            found.append(current)
        current = None

for c, a in sorted(set(found)):
    print(f"{c}:{a}")
PY
)"

  if [[ -z "$pairs" ]]; then
    warn "KDE App Menu widget not found in current Plasma layout."
    return
  fi

  while IFS=: read -r c a; do
    [[ -z "$c" || -z "$a" ]] && continue
    run_cmd "$kwrite --file \"$appletrc\" --group Containments --group \"$c\" --group Applets --group \"$a\" --group Configuration --group General --key icon vnde-menu"
    run_cmd "$kwrite --file \"$appletrc\" --group Containments --group \"$c\" --group Applets --group \"$a\" --group Configuration --group General --key customButtonText 'VNDE (KDE) POWER BY KDE'"
    run_cmd "$kwrite --file \"$appletrc\" --group Containments --group \"$c\" --group Applets --group \"$a\" --group Configuration --group General --key useCustomButtonText true"
  done <<< "$pairs"

  if command -v qdbus6 >/dev/null 2>&1; then
    run_cmd "qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'for (var i in desktops()) { desktops()[i].reloadConfig(); }' >/dev/null 2>&1 || true"
  elif command -v qdbus >/dev/null 2>&1; then
    run_cmd "qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'for (var i in desktops()) { desktops()[i].reloadConfig(); }' >/dev/null 2>&1 || true"
  fi

  log "KDE profile applied."
}

configure_gnome() {
  if ! command -v gsettings >/dev/null 2>&1; then
    warn "gsettings not found. Skip GNOME customization."
    return
  fi

  local wp="file://$HOME/.local/share/backgrounds/vietnam-dawn.svg"
  run_cmd "gsettings set org.gnome.desktop.background picture-uri '$wp'"
  run_cmd "gsettings set org.gnome.desktop.background picture-uri-dark '$wp'"
  run_cmd "gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'"
  run_cmd "gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita-dark'"
  run_cmd "gsettings set org.gnome.desktop.interface icon-theme 'Papirus-Dark'"
  run_cmd "gsettings set org.gnome.desktop.interface font-name 'Noto Sans 11'"
  run_cmd "gsettings set org.gnome.desktop.interface monospace-font-name 'Noto Sans Mono 11'"
  run_cmd "gsettings set org.gnome.desktop.interface clock-show-weekday true"
  run_cmd "gsettings set org.gnome.desktop.interface clock-format '24h'"
  run_cmd "gsettings set org.gnome.desktop.interface show-battery-percentage true"
  run_cmd "gsettings set org.gnome.desktop.wm.preferences button-layout 'appmenu:minimize,maximize,close'"

  run_cmd "gsettings set org.gnome.shell favorite-apps \"['vnde-file-manager.desktop','vnde-app-store.desktop','vnde-news.desktop','vnde-music.desktop','vnde-terminal.desktop','firefox.desktop','org.gnome.Software.desktop']\""

  run_cmd "gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings \"['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-menu/','/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-store/','/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-news/','/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-music/','/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-files/','/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-term-menu/','/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-shot/','/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-news-cli/']\""

  set_gnome_keybinding "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-menu/" "VN Menu" "vn-menu" "<Super>space"
  set_gnome_keybinding "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-store/" "VN App Center" "vn-app-store" "<Super>a"
  set_gnome_keybinding "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-news/" "VN News" "vn-news" "<Super>n"
  set_gnome_keybinding "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-music/" "VN Music" "vn-music" "<Super>m"
  set_gnome_keybinding "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-files/" "VN File Manager" "vn-file-manager" "<Super>e"
  set_gnome_keybinding "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-term-menu/" "VN Terminal Menu" "vn-terminal-context-menu" "<Ctrl><Alt>s"
  set_gnome_keybinding "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-shot/" "VN Screenshot" "flameshot gui" "Print"
  set_gnome_keybinding "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vnde-news-cli/" "VN News CLI" "vn-terminal -e vn-news-cli" "<Super><Shift>n"

  if command -v gnome-extensions >/dev/null 2>&1; then
    ext_list="$(gnome-extensions list 2>/dev/null || true)"
    if printf '%s\n' "$ext_list" | grep -q 'ubuntu-dock@ubuntu.com'; then
      run_cmd "gnome-extensions enable ubuntu-dock@ubuntu.com || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock show-favorites true || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock show-running true || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock isolate-workspaces false || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock isolate-monitors false || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock intellihide false || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock dock-fixed true || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock click-action 'minimize-or-previews' || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock running-indicator-style 'DOTS' || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock custom-theme-customize-running-dots true || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock custom-theme-running-dots-color '#ffffff' || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock custom-theme-running-dots-border-color '#ffffff' || true"
      run_cmd "gsettings set org.gnome.shell.extensions.dash-to-dock custom-theme-running-dots-border-width 0 || true"
    fi
    if printf '%s\n' "$ext_list" | grep -q 'appindicatorsupport@rgcjonas.gmail.com'; then
      run_cmd "gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com || true"
    fi
  fi

  log "GNOME profile applied."
}

install_openbox_session_legacy() {
  run_cmd "mkdir -p \"$HOME/.config/vnde/openbox\" \"$HOME/.config/vnde/tint2\" \"$HOME/.config/vnde/scripts\" \"$HOME/.local/share/xsessions\""
  run_cmd "cp \"$ROOT_DIR/vnde/openbox/rc.xml\" \"$HOME/.config/vnde/openbox/rc.xml\""
  run_cmd "cp \"$ROOT_DIR/vnde/tint2/tint2rc\" \"$HOME/.config/vnde/tint2/tint2rc\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/autostart.sh\" \"$HOME/.config/vnde/scripts/autostart.sh\""
  run_cmd "cp \"$ROOT_DIR/vnde/scripts/vnde-session\" \"$HOME/.local/bin/vnde-session\""
  run_cmd "chmod +x \"$HOME/.config/vnde/scripts/autostart.sh\" \"$HOME/.local/bin/vnde-session\""

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY ] write %s\n' "$HOME/.local/share/xsessions/vnde.desktop"
    printf '[DRY ] install %s\n' "/usr/share/xsessions/vnde.desktop"
  else
    cat > "$HOME/.local/share/xsessions/vnde.desktop" <<DESKTOP
[Desktop Entry]
Name=VNDE (Openbox Legacy)
Comment=Legacy VNDE session on Openbox
Exec=$HOME/.local/bin/vnde-session
TryExec=openbox
Type=Application
DesktopNames=VNDE
DESKTOP
    tmp="$HOME/.cache/vnde.desktop"
    mkdir -p "$HOME/.cache"
    cp "$HOME/.local/share/xsessions/vnde.desktop" "$tmp"
    run_cmd "sudo install -Dm644 \"$tmp\" /usr/share/xsessions/vnde.desktop || true"
  fi
}

print_done() {
  local session_name
  if [[ "$PROFILE" == "kde" ]]; then
    session_name="VNDE (KDE)"
  else
    session_name="VNDE"
  fi

  cat <<DONE

VNDE cai dat xong theo profile: $PROFILE

Sau khi cai:
1) Dang xuat.
2) O login, chon session: $session_name.
3) Dang nhap lai.

Phim tat:
- Super + Space: VN Menu
- Super + A: VN App Center
- Super + N: VN News (GUI)
- Super + Shift + N: VN News CLI (Terminal)
- Super + M: VN Music (GUI)
- Super + E: VN File Manager
- Ctrl + Alt + S: VN Terminal Menu
- Print: Flameshot

Lenh terminal:
- vnde                        # lenh tong VNDE (install/update/menu/terminal...)
- vnde-install                # cai/ap dung VNDE (mac dinh GNOME)
- vnde install --profile kde  # cai/ap dung VNDE (KDE)
- vnde-update                 # cap nhat source + ap dung lai config VNDE
- vnde-bootstrap              # bootstrap tu repo roi cai tu dong
- Alt + g trong VN Terminal   # tim nhanh tren internet
- Chuot phai trong VN Terminal # mo menu Copy/Paste/Search/Read-only
DONE
}

main() {
  log "Installing VNDE profile: $PROFILE"
  local pm
  pm="$(get_pm)"
  log "Detected package manager: $pm"

  if [[ "$NO_PACKAGES" -eq 0 ]]; then
    if [[ "$PROFILE" == "gnome" ]]; then
      install_packages_gnome "$pm"
    else
      install_packages_kde "$pm"
    fi
    setup_services
  fi

  install_shared_files
  configure_locale

  if [[ "$PROFILE" == "gnome" ]]; then
    install_vnde_gnome_session
    configure_gnome
  else
    install_vnde_kde_session
    configure_kde
  fi

  print_done
}

main
