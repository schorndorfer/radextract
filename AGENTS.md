# Agents and automated helpers

This repository uses small automated "agents" (scripts and utilities) to help run, test, and debug the CLI and related code. This document explains their roles, how to run them, and how to debug the CLI locally.

## Goals
- Make it easy to run and validate the `radex` CLI locally.
- Provide a lightweight, reproducible debug runner and tests so contributors can step through behavior.
- Document where automated edits and helpers live and how to extend them.

## Key agents / helpers in this repo
- CLI (cyclopts): implemented in `src/rad_extract/cli.py`. The cyclopts `App` object is exposed as `app` and the package entrypoint `main()` is exported by `rad_extract`.
- Tests: `tests/` contains pytest tests that exercise basic CLI import and help printing.
- Debug runner (recommended): optional small script you can add (see "Debugging and running locally").

## How to run the CLI locally
This project uses `uv` / `uv_build` entrypoints. With the project's virtualenv active (the repo stores a `.venv`), you can run:

```bash
# Show help
uv run radex --help

# Run extract on a single file
uv run radex extract /path/to/report.txt

# Run batch command
uv run radex batch /path/to/reports_dir --pattern "*.txt"
```

If you prefer to run the CLI module directly (useful for debugging), create a small runner script and run it with the project Python interpreter.

## Debugging and running under a debugger
Recommended: create `debug_runner.py` in the repo root with a short invocation and run it under `pdb` or your IDE.

Example `debug_runner.py`:

```python
from rad_extract import main
import sys

# Example to exercise the 'extract' command with a sample path
sys.argv = ["radex", "extract", "path/to/example.txt"]
main()
```

Run it under the venv Python with pdb:

```bash
.venv/bin/python -m pdb debug_runner.py
```

In VS Code, add a `launch.json` entry that runs the same script with the workspace venv as the interpreter and set breakpoints in `src/rad_extract/cli.py`.

## Tests
Run tests with pytest inside the project's venv:

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/pytest -q
```

The tests in `tests/` are intentionally small smoke tests validating that:
- the CLI module imports
- the `app` exists and exposes `extract` and `batch` commands
- the help output contains expected command names

## Contributing changes to agents
- Keep agent scripts simple and well-documented.
- If the cyclopts API changes, prefer to either pin a compatible cyclopts version in `pyproject.toml` or adapt the CLI to the installed API (this repo currently adapts the CLI to the installed cyclopts API).
- Add unit tests when changing CLI behavior.

## Contact / follow-ups
If you want, I can:
- Add the `debug_runner.py` and a VS Code `launch.json` to the repo and commit them.
- Add more thorough tests for argument parsing and path validation.

Happy to add whichever helper you'd like next.
