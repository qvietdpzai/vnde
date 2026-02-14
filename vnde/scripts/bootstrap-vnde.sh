#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${VNDE_REPO_URL:-https://github.com/<your-org>/<your-repo>.git}"
SRC_DIR="${VNDE_SOURCE_DIR:-$HOME/.local/share/vnde/source}"

echo "[VNDE] Bootstrap tu: $REPO_URL"

if [[ "$REPO_URL" == *"<your-org>"* || "$REPO_URL" == *"<your-repo>"* ]]; then
  echo "[VNDE] Hay set repo that:"
  echo "  export VNDE_REPO_URL='https://github.com/<org>/<repo>.git'"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y git
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y git
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm git
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper install -y git
  else
    echo "[VNDE] Khong tim thay package manager de cai git."
    exit 1
  fi
fi

mkdir -p "$(dirname "$SRC_DIR")"
if [[ -d "$SRC_DIR/.git" ]]; then
  git -C "$SRC_DIR" pull --ff-only || true
else
  rm -rf "$SRC_DIR.tmp"
  git clone --depth 1 "$REPO_URL" "$SRC_DIR.tmp"
  rm -rf "$SRC_DIR"
  mv "$SRC_DIR.tmp" "$SRC_DIR"
fi

install -Dm755 "$SRC_DIR/vnde/scripts/vnde" "$HOME/.local/bin/vnde"
sudo install -Dm755 "$SRC_DIR/vnde/scripts/vnde" /usr/local/bin/vnde || true

export VNDE_SOURCE_DIR="$SRC_DIR"
exec "$HOME/.local/bin/vnde" install "$@"
