#!/usr/bin/env bash
# Adds LinRAR to your application menu (like installing balenaEtcher).
# Run this from inside the LinRAR-linux-x64 folder, wherever you've placed it.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/linrar.desktop" <<EOF2
[Desktop Entry]
Type=Application
Name=LinRAR
Comment=Open, create and manage archives (zip, tar, rar, 7z...)
Exec=$DIR/LinRAR %f
Icon=archive-manager
Terminal=false
Categories=Utility;Archiving;
MimeType=application/zip;application/x-tar;application/gzip;application/x-bzip2;application/x-xz;application/x-rar;application/x-7z-compressed;
EOF2

update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
echo "LinRAR added to your application menu."
echo "You can also just double-click the 'LinRAR' file in this folder to run it directly."
