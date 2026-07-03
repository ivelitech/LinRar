<div align="center">

# LinRAR

**The archive manager Linux deserves.**

Open. Create. Extract. Done.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux-blue.svg)](#)
[![Version](https://img.shields.io/badge/version-0.0.5-orange.svg)](#)

</div>

---

## About

LinRAR is a free, open-source archive manager for Linux — a WinRAR-style
toolbar, a folder-style browser, and drag-and-drop support, built as a
single self-contained Python application with no required third-party
dependencies.

It's licensed under the MIT License. Read the code, change it, ship
your own fork — it's yours as much as anyone's.

## Features

- Drag and drop an archive onto the window to open it, or use the
  Open Archive button
- Browse archives like folders — navigate in and out of directories
- Create new archives, add files to existing ones
- Extract everything, or just the files you select
- Test archive integrity, preview files, search by name
- Best-effort repair of damaged ZIP archives
- Optional, dismissible in-app note about supporting development —
  no locked features, no trial period, ever

## Supported formats

| Format | Open | Create |
|---|---|---|
| ZIP | ✅ | ✅ |
| TAR / TAR.GZ / TAR.BZ2 / TAR.XZ | ✅ | ✅ |
| RAR | ✅ (needs `unrar` installed) | — |
| 7Z | ✅ (needs `p7zip` installed) | — |

RAR and 7Z are proprietary formats without an open specification for
writing archives, so — like most open-source archive tools — LinRAR
supports opening them but not creating new ones.

## Getting LinRAR

**Prebuilt binary (recommended for most users):** grab the latest
`LinRAR-linux-x64` release — it's a self-contained folder, no Python
or dependencies required. Unzip it and open the app.

**Running from source:** LinRAR is a single file, `linrar.py`, built
on the Python standard library. You'll need Python 3 with Tk support
(`python3-tk` on most distros). Drag-and-drop support additionally
needs the optional `tkinterdnd2` package from `requirements.txt` —
without it, LinRAR still runs fine, just without OS-level drag-and-drop.

An `install.sh` script is included that checks for these dependencies,
installs what it can, and registers LinRAR in your application menu.

## Building a standalone binary

The release binaries are built with [PyInstaller](https://pyinstaller.org):

```
pyinstaller --onedir --windowed --name LinRAR --collect-all tkinterdnd2 linrar.py
```

This produces a self-contained `dist/LinRAR/` folder that runs without
a system Python install.

## Project structure

- `linrar.py` — the entire application: an `Archive` backend class
  (format-specific read/write/list/test logic) and a `LinRARApp` GUI
  class (Tkinter-based, format-agnostic)
- `install.sh` — sets up LinRAR to run from source with menu integration
- `requirements.txt` — the one optional dependency (drag-and-drop)

## Contributing

Bug reports, feature requests, and pull requests are welcome — see
[CONTRIBUTING.md](CONTRIBUTING.md) for details on how the codebase is
organized and what makes a good contribution.

## License

MIT — see [LICENSE](LICENSE). Use it, modify it, ship it, just keep
the license notice attached.

---

<div align="center">

**LinRAR** — made for Linux, by people who use Linux.

</div>
