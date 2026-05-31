# Contributing to ECC Manager

Thanks for helping improve ECC Manager.

## Local Setup

Use Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

Run the Web UI locally:

```bash
ecc-manager --no-open
```

Run tests:

```bash
python3 -m unittest
```

Build the package:

```bash
python3 -m build
```

Validate PyPI metadata:

```bash
python3 -m twine check dist/*
```

## Pull Requests

- Keep changes focused and explain the user-facing behavior they affect.
- Add or update tests for changes to planning, application, Doctor checks, API handlers, or localization helpers.
- Do not commit local project lock files, generated instruction files, caches, virtual environments, or personal paths.
- Preserve local-first safety: Web UI write actions should remain protected by the local session token and should regenerate plans server-side before applying changes.

## Documentation

`README.md` is bilingual and should keep the `English | 简体中文` jump links working. The detailed Chinese guide lives in `docs/USER_GUIDE.md`.
