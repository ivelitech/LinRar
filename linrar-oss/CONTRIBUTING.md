# Contributing to LinRAR

Thanks for considering contributing — LinRAR is built for the people who
use it, and that includes the people who want to improve it.

## Ways to contribute

- **Bug reports.** Open an issue with your distro, desktop environment,
  the archive format involved, and steps to reproduce. Logs help.
- **Feature requests.** Open an issue describing the problem you're
  trying to solve, not just the feature — sometimes there's a simpler
  fix than the one you had in mind.
- **Pull requests.** Bug fixes, new format support, performance
  improvements, and UI polish are all welcome.

## Development setup

LinRAR is a single-file Python application (`linrar.py`) built on the
standard library, plus one optional dependency for drag-and-drop
(`tkinterdnd2`). There's no build step for running it from source —
just make sure `python3-tk` is installed on your system, install the
optional dependency from `requirements.txt` if you want drag-and-drop
while developing, and run the file directly.

## Code style

- Keep it dependency-light. The zero-install philosophy is core to the
  project — think twice before adding a new required dependency.
  Optional, gracefully-degrading dependencies (like drag-and-drop) are
  fine.
- Match the existing structure: the `Archive` class handles all
  format-specific logic; `LinRARApp` handles the UI and stays
  format-agnostic.
- Prefer small, focused pull requests over large ones — they're easier
  to review and easier to revert if something's wrong.

## Reporting security issues

If you find a security issue (for example, a path traversal risk when
extracting archives), please open an issue clearly marked as a security
report rather than a public exploit write-up, so it can be addressed
before wide disclosure.

## Code of conduct

Be respectful. Assume good faith. Disagreements about code are fine;
disrespect toward people isn't.
