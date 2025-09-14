"""Command-line interface for ProcMonD."""

#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton
from __future__ import annotations

import argparse
import sys

from rich.console import Console

from procmond.daemon import check_alerts, get_processes, store_records
from procmond.daemon import main as daemon_main

console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="procmond",
        description="ProcMonD - A lightweight process monitoring daemon",
    )

    # Use parse_known_args approach to avoid pytest collisions

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Daemon command - runs full monitoring loop
    daemon_parser = subparsers.add_parser("daemon", help="Run the full monitoring daemon")
    daemon_parser.add_argument("--config", help="Path to configuration file", default=None)

    # Smoke command - single run smoke test
    smoke_parser = subparsers.add_parser("smoke", help="Run single-pass smoke test")
    smoke_parser.add_argument("--config", help="Path to configuration file", default=None)

    return parser


def run_daemon() -> None:
    """Run the full daemon monitoring loop."""
    daemon_main()


def run_smoke() -> None:
    """Run a single smoke test pass."""
    console.print("Running smoke test...")
    processes = get_processes()
    console.print(f"Found {len(processes)} processes")

    # Show first 5 processes for verification
    for p in processes[:5]:
        try:
            console.print(p.to_dict)
        except (AttributeError, TypeError) as e:
            console.print(f"Error serializing process: {e}")

    # Store records to create database if needed
    store_records(processes)

    # Check for alerts
    alerts = check_alerts()
    console.print(f"Found {len(alerts)} alerts")
    for a in alerts[:5]:
        console.print(a)


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()

    # Parse known args to avoid conflicts with pytest
    args, _unknown = parser.parse_known_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "daemon":
        run_daemon()
    elif args.command == "smoke":
        run_smoke()
    else:
        parser.print_help()
        sys.exit(1)


# Convenience function for smoke entry point
def smoke() -> None:
    """Entry point for procmond-smoke command."""
    run_smoke()


if __name__ == "__main__":
    main()
