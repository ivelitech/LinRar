set -e

INSTALL_DIR="$HOME/.local/share/linrar"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Installing LinRAR..."


if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is required but not found. Install it with your package manager, e.g.:"
    echo "  sudo apt install python3        (Debian/Ubuntu)"
    echo "  sudo dnf install python3        (Fedora)"
    echo "  sudo pacman -S python           (Arch)"
    exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "Tkinter is missing. Attempting to install it (you may be prompted for your password)..."
    if command -v apt >/dev/null 2>&1; then
        sudo apt install -y python3-tk
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3-tkinter
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm tk
    else
        echo "Please install the 'tkinter' package for your distro manually, then re-run this installer."
        exit 1
    fi
fi


python3 -c "import tkinterdnd2" >/dev/null 2>&1 || \
    pip3 install --user tkinterdnd2 >/dev/null 2>&1 || \
    echo "(Optional drag-and-drop support not installed — LinRAR will still work fine.)"


mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR"
cp "$(dirname "$0")/linrar.py" "$INSTALL_DIR/linrar.py"
chmod +x "$INSTALL_DIR/linrar.py"

cat > "$BIN_DIR/linrar" <<EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/linrar.py" "\$@"
EOF
chmod +x "$BIN_DIR/linrar"


cat > "$DESKTOP_DIR/linrar.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=LinRAR
Comment=Open, create and manage archives (zip, tar, rar, 7z...)
Exec=$BIN_DIR/linrar %f
Icon=archive-manager
Terminal=false
Categories=Utility;Archiving;
MimeType=application/zip;application/x-tar;application/gzip;application/x-bzip2;application/x-xz;application/x-rar;application/x-7z-compressed;
EOF

update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true

echo ""
echo "Done. LinRAR is installed."
echo "  - Run it from a terminal:  linrar"
echo "  - Or find 'LinRAR' in your application menu."
echo "  - Open an archive directly: linrar somefile.zip"
echo ""
echo "(If '$BIN_DIR' isn't on your PATH, add this to your ~/.bashrc or ~/.zshrc:"
echo '  export PATH="$HOME/.local/bin:$PATH"'
echo ")"
