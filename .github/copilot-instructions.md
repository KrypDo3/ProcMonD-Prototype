# Copilot / AI agent instructions for ProcMonD-Prototype

Purpose: Give AI coding agents the essential, project-specific knowledge needed to be immediately productive.

Quick start (dev machine: Windows PowerShell):

```powershell
& .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# single-run smoke harness (does not start daemon loop)
python run_smoke.py
# run full tests
python -m pytest -q
```

Big picture (core components):

- `procmond.py` — application entrypoint. Contains process collection, DB writes, detector invocation, and daemon startup. On Unix this uses `python-daemon`; on Windows there is a no-op fallback to allow local dev.
- `ConfigManager.py` — central config loader for INI files and CLI flags. Note: code uses `parse_known_args()` to avoid pytest arg collisions.
- `Detectors.py` — detectors are implemented as functions that run SQL queries against the latest snapshot in the SQLite DB (`procmond.db`) and return `AppDataTypes.Alert` instances. Keep imports lazy (inside the detector function) to avoid circular imports.
- `AppDataTypes/ProcessRecord.py` & `AppDataTypes/Alert.py` — data classes used across the project. `ProcessRecord` handles file existence and hashing; it reads `hash_buffer_size` from runtime config (lazy access).
- `AlertHandlers/` — delivery adapters: `EmailAlertHandler.py`, `SyslogAlertHandler.py`, `WebHookAlertHandler.py`. `WebHookAlertHandler` uses `requests.post`; `SyslogAlertHandler` includes a Windows-friendly logging fallback when `syslog` is unavailable.
- `procmond.db` — SQLite DB storing snapshots used by detectors. Tests create temporary DBs and monkeypatch `ConfigManager` to point `database_path` at them.

Project-specific conventions and important patterns:

- Avoid import-time work that triggers platform-specific imports. Many modules use lazy imports (import inside functions) to prevent POSIX-only modules (e.g., `pwd`, `syslog`) from breaking Windows development.
- Tests run under `pytest`; code must tolerate unknown CLI args. `ConfigManager` uses `parse_known_args()` to avoid `SystemExit` in test runs.
- Detectors are SQL-centric: they assume a snapshot schema; write detectors as pure functions returning `Alert` objects. Example: `Detectors.detect_process_without_exe()` executes SQL and builds `AppDataTypes.Alert` on matches.
- Hashing: `ProcessRecord.hash()` reads `hash_buffer_size` from `procmond.config` at runtime. When editing hashing logic, preserve the default fallback buffer value to avoid breaking tests.
- DB and logging paths: defaults are `procmond.db` and `procmond.log` in repo root; respect `ConfigManager` overrides for tests and CI.

Integration points / external deps to be mindful of:

- `psutil` — process enumeration. Avoid heavy mocking; tests frequently create synthetic rows instead of mocking `psutil` deep internals.
- `requests` — used by `WebHookAlertHandler`. Keep network calls simple and allow injection/monkeypatching in tests.
- `python-daemon` — used for Unix daemonization. Do not import at module top-level if you want cross-platform behavior; use a try/except with a safe fallback as in `procmond.py`.
- Email delivery uses SMTP in `EmailAlertHandler`; treat mail delivery as integration work and prefer mocking in tests.

Developer workflows (commands & tips):

- Activate venv in PowerShell: `& .\.venv\Scripts\Activate.ps1`.
- Run smoke harness: `python run_smoke.py` — quick single-run that collects processes, writes to DB, and prints sample alerts.
- Run unit tests: `python -m pytest -q`. Tests assume you use the venv.
- When updating dependencies: update `requirements.txt` (conservative ranges) and regenerate `requirements.lock` using `pip freeze > requirements.lock` in the venv.
- DO NOT run syntactic mass-upgrade tools (e.g. `pyupgrade`) against the venv directory — exclude `.venv` to avoid rewriting site-packages.

Debugging hints specific to this repo:

- Import-time failures on Windows are often due to POSIX imports (`pwd`, `syslog`, `daemon`). Look for those imports and prefer lazy import or platform guards.
- Circular imports between `procmond`, `Detectors`, and `ProcessRecord` were solved here by moving config access and some imports inside functions. If you add cross-module references, prefer `from . import X` inside functions and use `sys.modules` fallbacks only when necessary.
- DB issues: tests create temporary DBs and set `ConfigManager.database_path`. Use the same approach when writing test fixtures.

Files to read first (high signal):

- `procmond.py` — entrypoint and main process logic
- `Detectors.py` — shows detector pattern and SQL usage
- `AppDataTypes/ProcessRecord.py` and `AppDataTypes/Alert.py` — core data shapes
- `AlertHandlers/` — examples of external interaction (requests, syslog, SMTP)
- `ConfigManager.py` — config knobs used across the app
- `run_smoke.py` and `tests/` — quick examples of how the project is exercised in CI/local runs

When submitting patches or PRs:

- Run the smoke harness and tests locally before pushing.
- Keep dependency changes conservative (range updates) and include a regenerated `requirements.lock` when pinning is intended.
- Preserve Windows-friendly fallbacks unless the change is explicitly Linux-only.

If anything above is unclear or you want additional examples (small code snippets showing lazy imports, a sample detector, or a small CI workflow), tell me which section to expand and I will iterate.

## Python style & linting (ruff + typing)

- Linter/formatter: the project uses ruff as the single, source-of-truth linter/formatter. AI edits should be ruff-compliant. If you add new lint rules, include a suggested `pyproject.toml` snippet in the PR and keep rules conservative.
- Type annotations: add type annotations wherever possible. Public functions, class methods, and module-level APIs must have explicit parameter and return type annotations. Use `from __future__ import annotations` at the module top for forward refs and to keep runtime costs low.
- Minimal rules to follow when contributing:
  - Use typed signatures for all new functions and methods. Small private helpers used only inside a function may omit annotations if justified, but prefer annotating anyway.
  - Avoid `Any` unless there is a clear interoperability or third-party constraint; add `# type: ignore` with a short justification when you must.
  - Annotate class attributes and dataclasses. For data containers in `AppDataTypes/`, prefer explicit typing over implicit attributes.
  - Prefer `Path` from `pathlib` for filesystem paths in signatures instead of raw `str`.
  - Use `Optional[T]` rather than `Union[T, None]`. Use `collections.abc` types for callables/iterables when appropriate.
  - Keep functions small and side-effect free where possible (Detectors should be pure SQL-to-Alert transformers).
- Suggested ruff configuration (to include in `pyproject.toml` or `.ruff.toml`):

```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "C90", "ANN", "S", "RET"]
extend-select = ["I"]
ignore = ["E203"]
# Keep autofixes enabled for safe rules during local dev
fix = true
```

- Optional: add static type checking in CI with `mypy` or `pyright` and enable strict options for changed files. A minimal `mypy` snippet to consider for `pyproject.toml`:

```toml
[tool.mypy]
python_version = 3.11
strict = true
exclude = "(.venv|procmond.db|procmond.log)"
```

- Why these rules matter for this repo:
  - The code uses small, testable transformers (detectors) that benefit from type-driven refactors.
  - Lazy imports and platform guards make some runtime shapes dynamic; explicit typing documents expected types and reduces accidental API breakage.

If you'd like, I can also:

- create a `pyproject.toml` with the ruff config above,
- add a `.github/workflows/ci.yml` that runs `ruff check`, `python -m pytest -q`, and `mypy` (optional),
- or run ruff across the repo and open a PR with automatic fixes.

If you prefer a different line length or stricter/looser ruff rule set, tell me the preferred values and I'll update the doc and config.
