# AGENTS.md

## Setup commands

- Install deps: `pip install -r requirements.txt`
- Activate venv: `source .venv/bin/activate` (Linux/macOS) or `& .\.venv\Scripts\Activate.ps1` (Windows)
- Start dev server: `python run_smoke.py` (single-run smoke test)
- Run tests: `python -m pytest -q`

## Code style

- Python 3.10+ with type annotations
- Use `from __future__ import annotations` for forward refs
- Single quotes, 100 character line length
- Use functional patterns where possible (detectors as pure SQL-to-Alert transformers)
- Lazy imports inside functions to avoid platform-specific import errors

## Testing instructions

- Run smoke test: `python run_smoke.py` (single run, no daemon loop)
- Run full test suite: `python -m pytest -q`
- Run specific test: `python -m pytest tests/test_detectors.py -v`
- Tests create temporary DBs and monkeypatch `ConfigManager.database_path`
- Prefer synthetic data over heavy mocking of `psutil` internals
- All code changes must include appropriate tests

## Project overview

ProcMonD-Prototype is a lightweight process tripwire daemon that inspects running processes for signs of compromise. Core architecture:

- **`procmond.py`** — Main daemon entry point with process collection and monitoring loop
- **`ConfigManager.py`** — INI-based configuration loader with CLI argument support
- **`Detectors.py`** — SQL-based detection functions that identify suspicious process behaviors
- **`AppDataTypes/`** — Core data models (`ProcessRecord`, `Alert`)
- **`AlertHandlers/`** — Pluggable alert delivery systems (syslog, email, webhook)

## Development workflow

- Use `python run_smoke.py` for quick single-run testing (no daemon loop)
- Use `python procmond.py` for full daemon with debug output
- Monitor database: `ls -la procmond.db procmond.log`
- Format code: `ruff format`
- Lint code: `ruff check`
- Type check: `mypy .` (if configured)

## Platform compatibility

- **Cross-platform**: Code must work on both Linux/macOS and Windows
- **Unix Features**: `python-daemon`, `syslog` modules have Windows-safe fallbacks
- **Lazy Loading**: Import platform-specific modules inside functions with try/except blocks
- **ConfigManager**: Uses `parse_known_args()` to avoid pytest argument collisions

## Detector development

- **Pure Functions**: Detectors should be SQL-to-Alert transformers
- **Lazy Config**: Import `procmond.config` inside detector functions to avoid circular imports
- **Database Schema**: Assume the processes table schema defined in `store_records()`
- **Example Pattern**: `Detectors.detect_process_without_exe()` executes SQL and builds `AppDataTypes.Alert` on matches

## Security considerations

- Avoid import-time work that triggers platform-specific imports
- Preserve Windows-friendly fallbacks unless change is explicitly Linux-only
- Use specific exceptions; graceful degradation for platform-specific features
- Treat mail delivery as integration work and prefer mocking in tests

## Common gotchas

- Import-time failures on Windows often due to POSIX imports (`pwd`, `syslog`, `daemon`)
- Circular imports solved by moving config access inside functions
- DB issues: tests create temporary DBs and set `ConfigManager.database_path`
- When updating dependencies: update `requirements.txt` and regenerate `requirements.lock`

## Files to read first

- `procmond.py` — Main daemon logic and process collection
- `Detectors.py` — Detection algorithms and SQL patterns
- `AppDataTypes/ProcessRecord.py` — Core data model with file operations
- `ConfigManager.py` — Configuration loading and CLI argument handling
- `run_smoke.py` — Quick examples of project exercise patterns
