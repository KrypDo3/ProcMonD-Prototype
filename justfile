#!/usr/bin/env just --working-directory .
# ProcMonD-Prototype Development Tasks
# Run `just --list` to see available tasks

set shell := ["bash", "-cu"]
set windows-powershell := true
set dotenv-load := true
set ignore-comments := true

# --------------------------------
# Default variables
# --------------------------------
default:
    @just --choose

alias h := help

help:
    just --summary

# --------------------------------
# === Formatting ===
# --------------------------------

# 🚀 Full code + commit checks
check: lint pre-commit basedpyright
    @uv lock --locked

# Run basedpyright type checking on all packages
basedpyright:
    cd {{ justfile_dir() }}
    uv run basedpyright -p pyproject.toml

format:
    cd {{ justfile_dir() }}
    uv run ruff format
    uv run --group ci mdformat --exclude '.venv/**' --exclude 'node_modules/**' --exclude 'dist/**' --exclude 'build/**' .

pre-commit:
    cd {{ justfile_dir() }}
    uv run pre-commit run -a

# Check code formatting using ruff
format-check:
    uv run ruff format --check

# Run all linting checks
lint: format-check
    uv run ruff check

megalinter:
    cd {{ justfile_dir() }}
    npx mega-linter-runner --flavor python
    just remove-mega-linter-reports

[unix]
remove-mega-linter-reports:
    rm -rf mega-linter-reports/

[windows]
remove-mega-linter-reports:
    Remove-Item -Path mega-linter-reports/ -Recurse -Force -ErrorAction SilentlyContinue

megalinter-fix:
    cd {{ justfile_dir() }}
    npx mega-linter-runner --flavor python --fix
    just remove-mega-linter-reports

bandit:
    cd {{ justfile_dir() }}
    uv run bandit -c .bandit.yml -r .

# --------------------------------
# === Testing ===
# --------------------------------

# Run all tests
test: test-unit cli-smoke

# Run unit tests
@test-unit:
    uv run python -m pytest -q

# Run smoke test using script (legacy compatibility)
@smoke:
    uv run python scripts/run_smoke.py

# Run smoke test using CLI
@cli-smoke:
    uv run procmond smoke

# --------------------------------
# === Development ===
# --------------------------------

# Run daemon via CLI in foreground for debugging
@dev-daemon:
    uv run procmond daemon

# Run daemon via Python module for debugging
@dev-run:
    uv run python -m procmond.cli daemon

# --------------------------------
# === Maintenance ===
# --------------------------------

# Lint the justfile itself
@just-lint:
    just --fmt --check --unstable

# Clean up generated files
clean:
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    rm -f procmond.db procmond.log

# Show project status
@status:
    echo "=== ProcMonD Project Status ==="
    echo "Python version: $(uv run python --version)"
    echo "Package structure:"
    find src -name "*.py" | head -10
    echo "Dependencies:"
    uv pip list 2>/dev/null | head -10 || echo "uv environment not found"
    echo ""
    echo "Database and logs:"
    ls -la procmond.db procmond.log 2>/dev/null || echo "No database or log files found"
    echo "Tests status:"
    uv run python -m pytest --collect-only -q 2>/dev/null | tail -1 || echo "pytest collection failed"


# --------------------------------
# === Deployment ===
# --------------------------------

build:
    uv build


ci-check: check test build
