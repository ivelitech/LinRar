# LinRAR v0.0.1

**First public release.**

This is the initial release of LinRAR — a free, open-source archive
manager built for Linux. It's early, it's fresh off the workbench, and
it already does the job.

---

## Highlights

- **Zero-install launch.** Download the folder, open the app, you're
  in. No package manager, no dependency wrangling, no terminal.
- **A file browser, not a file list.** Archives open like folders —
  navigate in and out of directories the way you already think about
  files.
- **The essentials, done properly.** Create archives, add to them,
  extract everything or just what you select, verify integrity, preview
  a file, search by name, and recover what's salvageable from a
  damaged archive.
- **Broad format support out of the box.** Full read/write for ZIP and
  the TAR family (TAR, TAR.GZ, TAR.BZ2, TAR.XZ). Open-only support for
  RAR and 7Z.
- **Genuinely portable.** The whole app is one self-contained folder.
  Copy it, move it, run it from a USB drive — it doesn't leave a trace
  on the system it isn't currently running on.

## What's inside this release

| Format | Open | Create |
|---|---|---|
| ZIP | ✅ | ✅ |
| TAR / TAR.GZ / TAR.BZ2 / TAR.XZ | ✅ | ✅ |
| RAR | ✅ | — |
| 7Z | ✅ | — |

## Known limitations

This is a v0.0.1 — an early release, not a finished product.

- RAR and 7Z are open-only, by design, since both are closed formats
  without a free specification for writing archives.
- Adding files to an already-compressed TAR archive rebuilds the whole
  archive behind the scenes, which can be slow on very large archives.
- Repair support currently covers ZIP archives only.
- No signed release build yet — your system may ask you to confirm
  before running it the first time.

## A note on where this is headed

v0.0.1 is a foundation, not a finish line. The goal is an archive
manager that stays out of your way and never asks you to think about
it — this release is the first real step toward that, and it's stable
enough to use today.

Feedback, bug reports, and ideas are welcome. This project is built
for the people who use it.

---

*Thank you for trying LinRAR.*
