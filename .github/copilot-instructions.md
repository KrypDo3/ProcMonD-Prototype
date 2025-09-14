# Copilot / AI agent instructions for ProcMonD-Prototype


# Essential Guide for AI Coding Agents

## Architecture & Major Components
ProcMonD-Prototype is a cross-platform process monitoring daemon. It inspects running processes for compromise, records metadata to SQLite, and delivers alerts via syslog, email (SMTP), or HTTP webhook. The codebase is modular:

- **Entrypoint:** `procmond.py` (legacy), `src/procmond/cli.py` (CLI), `src/procmond/daemon.py` (daemon loop)
- **Config:** `src/procmond/core/config_manager.py` loads INI config and CLI flags, using `parse_known_args()` to avoid test collisions
- **Detectors:** `src/procmond/core/detectors.py` implements SQL-based detection functions (pure transformers: SQL → Alert)
- **Models:** `src/procmond/models/process_record.py` and `alert.py` define core data shapes; `ProcessRecord` handles file existence and hashing
- **Alert Handlers:** `src/procmond/handlers/` (email, syslog, webhook) provide pluggable delivery, with platform-safe fallbacks
- **Database:** SQLite (`procmond.db`) stores process snapshots; detectors query latest state

## Developer Workflows
- **Setup:**
  - Activate venv: `source .venv/bin/activate` (macOS/Linux) or `& .\.venv\Scripts\Activate.ps1` (Windows)
  - Install deps: `pip install -r requirements.txt`
- **Smoke test:** `python scripts/run_smoke.py` (single-run, prints sample alerts)
- **Run full tests:** `python -m pytest -q` (tests auto-create temp DBs, monkeypatch config)
- **Lint/format:** `ruff format` and `ruff check` (see `pyproject.toml`)
- **Type check:** `mypy .` (if configured)
- **Monitor DB/logs:** `ls -la procmond.db procmond.log`

## Project-Specific Patterns & Conventions
- **Lazy imports:** Place platform-specific imports (e.g., `pwd`, `syslog`, `daemon`) inside functions to avoid Windows import errors
- **Config access:** Always use `ConfigManager` for runtime config; detectors import config inside functions to avoid circular imports
- **Detectors:** Write as pure functions returning `Alert` objects; use SQL queries against latest DB snapshot
- **Hashing:** `ProcessRecord.hash()` reads buffer size from config at runtime; preserve default fallback
- **Alert delivery:** Handlers use platform guards and allow injection/mocking for tests
- **Testing:** Prefer synthetic DB rows over deep mocking of `psutil`; tests monkeypatch config paths
- **Paths:** Default DB/log paths are repo root; respect config overrides for tests/CI

## Integration Points
- **psutil:** Used for process enumeration; avoid heavy mocking
- **requests:** Used by webhook handler; keep network calls simple
- **python-daemon:** Used for Unix daemonization; import inside function with fallback
- **SMTP:** Email delivery; treat as integration, prefer mocking in tests

## Key Files & Directories
- `src/procmond/cli.py`, `daemon.py` — main logic
- `src/procmond/core/config_manager.py` — config loader
- `src/procmond/core/detectors.py` — detection logic
- `src/procmond/models/process_record.py`, `alert.py` — data models
- `src/procmond/handlers/` — alert delivery
- `scripts/run_smoke.py` — quick test harness
- `tests/` — unit tests, DB monkeypatching

## Style & Linting
- Python 3.10+ with type annotations
- Use `from __future__ import annotations` for forward refs
- Line length: 100 (see `pyproject.toml`)
- Prefer explicit types for public APIs and dataclasses
- Use `Path` for filesystem paths in signatures
- See `pyproject.toml` for ruff config

---
If any section is unclear or missing, please provide feedback so this guide can be further refined for AI agent productivity.
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
    - The codebase is cross-platform and may run in constrained environments; type annotations help catch issues early.
