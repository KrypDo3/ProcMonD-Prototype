#!/usr/bin/env python3

"""Main daemon module for ProcMonD.

This module contains the main daemon loop and process collection logic
for the ProcMonD process monitoring system.
"""

#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton

from __future__ import annotations

import sys
from datetime import UTC, datetime
from logging import basicConfig, fatal, getLogger
from pathlib import Path
from sqlite3 import OperationalError, connect
from time import sleep
from typing import TYPE_CHECKING, Any, Self

try:
    from daemon import DaemonContext as _DaemonContext

    DaemonContext: Any = _DaemonContext  # type: ignore[assignment]
except ImportError:
    # The 'python-daemon' package imports Unix-only modules (like 'pwd') at import time.
    # Provide a minimal, no-op fallback DaemonContext for non-Unix platforms (Windows)
    # so the program can run without requiring the full daemon behavior.
    class DaemonContext:
        """Fallback daemon context for non-Unix platforms."""

        def __init__(self) -> None:
            """Initialize the fallback daemon context."""
            self.detach_process = False
            self.stderr: object | None = None
            self.working_directory: str | Path | None = None

        def __enter__(self) -> Self:
            """Enter the daemon context."""
            return self

        def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: object) -> bool:
            """Exit the daemon context.

            :param exc_type: Exception type.
            :param exc: Exception instance.
            :param tb: Traceback object.
            :return: False to not suppress exceptions.
            """
            return False

        def close(self) -> None:
            """Close the daemon context."""
            return


from psutil import AccessDenied, NoSuchProcess, ZombieProcess, process_iter

from procmond.core import detectors
from procmond.core.config_manager import ConfigManager
from procmond.models.process_record import ProcessRecord

if TYPE_CHECKING:
    from procmond.models.alert import Alert

config = ConfigManager()
daemon_ctx = DaemonContext()
logger = getLogger(__name__)


def main() -> None:
    """The main function that is run when the process monitoring daemon starts up."""
    basicConfig(
        format=config.log_message_format,
        datefmt=config.log_message_datefmt,
        level=config.numeric_log_level,
    )
    with Path(config.log_file).open("w") as out_log:
        daemon_ctx.detach_process = False
        daemon_ctx.stderr = out_log
        daemon_ctx.working_directory = config.root_path
        with daemon_ctx:
            logger.info("ProcMonD monitoring service starting up.")
            logger.info("Storing in database: %s", config.database_path)
            if config.alert_to_syslog:
                logger.info("Logging to syslog")
            if config.alert_to_email:
                logger.info("Logging to email")
            if config.alert_to_webhook:
                logger.info("Logging to webhook")

            try:
                while True:
                    logger.debug("Performing process checks.")
                    process_records = get_processes()
                    store_records(process_records)
                    alerts = check_alerts()
                    if alerts:
                        action_alerts(alerts)

                    sleep(config.refresh_rate)
            except KeyboardInterrupt:
                daemon_ctx.close()
                sys.exit(-1)


def get_processes() -> list[ProcessRecord]:
    """Walk the current process list and return ProcessRecord objects.

    :return: The collection of process records.
    """
    process_records = []
    for process in process_iter():
        proc = ProcessRecord(process.pid)
        try:
            proc.name = process.name()
            proc.ppid = process.ppid()
            proc.path = process.exe()

        except AccessDenied:
            logger.warning("%s is not an accessible process.", proc)
            proc.valid = False
        except FileNotFoundError:
            logger.warning("%s executable could not be found.", proc)
            proc.valid = True
            proc.accessible = True
        except ZombieProcess:
            logger.warning("%s is a zombie process.", proc)
            proc.valid = False
        except NoSuchProcess:
            logger.warning("%s process no longer exists.", proc)
            proc.valid = False
        finally:
            if proc.valid is True:
                process_records.append(proc)

    return process_records


def store_records(process_records: list[ProcessRecord]) -> None:
    """Stores a List of ProcessRecord objects in a SQLite3 database.

    :param process_records: A List of ProcessRecords representing each process identified.
    """
    try:
        with connect(config.database_path) as conn:
            cur = conn.cursor()
            # Create the database if it doesn't already exist.
            cur.execute(
                "CREATE TABLE IF NOT EXISTS processes "
                "(id INTEGER, ppid INTEGER, updated_at DATETIME, name VARCHAR, path VARCHAR, "
                'valid BIT, "hash" VARCHAR, accessible BIT, file_exists BIT, '
                "CONSTRAINT processes_pk PRIMARY KEY (id, updated_at));"
            )
            cur.execute("CREATE INDEX IF NOT EXISTS processes_name_hash_index ON processes (name DESC, hash DESC);")
            cur.execute("CREATE INDEX IF NOT EXISTS processes_updated_at_index ON processes(updated_at DESC);")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS processes_file_exists_accessible_updated_at_index "
                "ON processes (file_exists, accessible, updated_at);"
            )
            cur.execute("CREATE INDEX IF NOT EXISTS processes_id_path_hash_index ON processes (id, path, hash);")
            conn.commit()

            # Now insert the new record.
            timestamp = datetime.now(UTC)
            insert_sql = (
                "INSERT INTO processes (id, ppid, updated_at, name, path, valid, hash, accessible, "
                "file_exists) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            )
            for p in process_records:
                if p.valid:
                    cur.execute(
                        insert_sql,
                        (
                            p.pid,
                            p.ppid,
                            timestamp,
                            p.name,
                            p.path,
                            p.valid,
                            p.hash,
                            p.accessible,
                            p.exists,
                        ),
                    )
            conn.commit()
    except OperationalError:
        fatal(f"Cannot write to database file {config.database_path}")
        daemon_ctx.close()
        sys.exit(-1)


def check_alerts() -> list[Alert]:
    """Run each alert test to see if anything is amiss.

    :return: A List of alerts.
    """
    alerts = []

    alerts.extend(detectors.detect_process_without_exe())
    alerts.extend(detectors.detect_process_with_hash_change())
    alerts.extend(detectors.detect_process_with_duplicate_name())
    return alerts


def action_alerts(alerts: list[Alert]) -> None:
    """Trigger each enabled action type on the list of Alerts.

    :param alerts: A List of Alert objects representing each alert to be processed.
    """
    if config.alert_to_syslog:
        from procmond.handlers.syslog_alert_handler import syslog_alert_handler  # noqa: PLC0415

        syslog_alert_handler(alerts)

    if config.alert_to_email:
        from procmond.handlers.email_alert_handler import email_alert_handler  # noqa: PLC0415

        email_alert_handler(alerts)

    if config.alert_to_webhook:
        from procmond.handlers.webhook_alert_handler import webhook_alert_handler  # noqa: PLC0415

        webhook_alert_handler(alerts)


if __name__ == "__main__":
    main()
