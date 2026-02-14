#!/usr/bin/env bash
set -euo pipefail

# Wallpaper + compositor + panel
feh --bg-fill "$HOME/.local/share/backgrounds/vietnam-dawn.svg" &
picom --experimental-backends --config /dev/null -b || true

# Notification daemon
command -v dunst >/dev/null 2>&1 && dunst &

# Input method for Vietnamese typing
if command -v ibus-daemon >/dev/null 2>&1; then
  ibus-daemon -drx &
  (sleep 2 && ibus engine Unikey >/dev/null 2>&1) &
fi

# Start panel
(tint2 -c "$HOME/.config/vnde/tint2/tint2rc" &) || true

# Tray applets for convenience
command -v nm-applet >/dev/null 2>&1 && nm-applet --indicator &
command -v pasystray >/dev/null 2>&1 && pasystray &
command -v blueman-applet >/dev/null 2>&1 && blueman-applet &
command -v udiskie >/dev/null 2>&1 && udiskie -t &
command -v volumeicon >/dev/null 2>&1 && volumeicon &

# Policy kit agent
if command -v /usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1 >/dev/null 2>&1; then
  /usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1 &
elif command -v lxqt-policykit-agent >/dev/null 2>&1; then
  lxqt-policykit-agent &
fi
