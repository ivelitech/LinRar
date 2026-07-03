# LinRAR

A WinRAR-style archive manager for Linux. Open, create, browse, add to, and
extract archives from a simple GUI — or from the command line.

Written in pure Python 3 + Tkinter, so it runs on essentially any Linux
distro with no extra dependencies for the core formats (zip, tar, tar.gz,
tar.bz2, tar.xz). Optional support for `.rar` and `.7z` (read/extract only,
since those are proprietary formats) if you have `unrar`/`unar` or
`p7zip` installed.

## Install

```bash
chmod +x install.sh
./install.sh
```

This installs LinRAR to `~/.local/share/linrar`, adds a `linrar` command to
`~/.local/bin`, and registers it as an app so it shows up in your
application menu and can be set as the default program for archive files
(right-click an archive in your file manager → Open With → LinRAR).

## Usage

```bash
linrar                  # launch the GUI, then use Open/New Archive
linrar myfile.zip        # open an archive directly
```

The interface mirrors WinRAR: a menu bar (File / Commands / Tools / Favorites /
Options / Help), an icon toolbar, a breadcrumb path bar with an Up button,
and a Name / Size / Type / Modified file listing you can navigate into
folders inside the archive just like a file manager.

Toolbar buttons:
- **Add** — add files into the current folder of an open archive
- **Extract To** — extract the whole archive to a folder you choose
- **Test** — verify archive integrity (CRC check)
- **View** — open the selected file with your system's default app
- **Delete** — remove selected entries from a zip/tar archive
- **Find** — search file names inside the archive
- **Wizard** — guided create/open flow
- **Info** — archive size, format, file/folder counts
- **Repair** — best-effort recovery of a damaged .zip

Double-click a folder row to browse into it; double-click a file to view it;
use the Up arrow (or Backspace) to go back up.

## Supported formats

| Format         | Create | Extract | Notes |
|----------------|:------:|:-------:|-------|
| `.zip`         | ✅ | ✅ | native |
| `.tar`         | ✅ | ✅ | native |
| `.tar.gz`/`.tgz`   | ✅ | ✅ | native |
| `.tar.bz2`/`.tbz2` | ✅ | ✅ | native |
| `.tar.xz`/`.txz`   | ✅ | ✅ | native |
| `.rar`         | ❌ | ✅ | needs `unrar` or `unar` installed |
| `.7z`          | ❌ | ✅ | needs `p7zip` installed |

RAR and 7z creation isn't included because those are closed/patented
formats without a free-software writer — this mirrors why most Linux
archive tools (File Roller, Ark, etc.) are also extract-only for `.rar`.

To add optional format support:
```bash
sudo apt install unrar p7zip-full     # Debian/Ubuntu
sudo dnf install unrar p7zip          # Fedora
sudo pacman -S unrar p7zip            # Arch
```

## Uninstall

```bash
rm -rf ~/.local/share/linrar
rm ~/.local/bin/linrar
rm ~/.local/share/applications/linrar.desktop
```

## Running without installing

You can also just run it directly, no install needed:
```bash
python3 linrar.py
```
(requires `python3-tk`, which is preinstalled on most desktop distros)
