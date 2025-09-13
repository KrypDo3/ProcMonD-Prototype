"""Detection algorithms for ProcMonD.

This module contains functions that detect suspicious process behavior
by analyzing the process database.
"""

#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton

from __future__ import annotations

from sqlite3 import connect

from procmond.models.alert import Alert


def detect_process_without_exe() -> list[Alert]:
    """Checks for processes with no corresponding executables on disk.

    :return: A List of Alerts for each process that has no associated executable.
    """
    # import config lazily to avoid circular import when daemon initializes
    from procmond.daemon import config  # noqa: PLC0415

    result = []
    with connect(config.database_path) as conn:
        cur = conn.cursor()
        sql = """SELECT id, updated_at, name, path, file_exists
                FROM processes
                WHERE file_exists = 0
                  AND accessible = 1
                  AND updated_at = (SELECT MAX(updated_at) FROM processes)
                ORDER BY updated_at DESC
                """
        cur.execute(sql)
        for record in cur:
            pid, _updated_at, name, file_path, _file_exists = record
            alert = Alert(
                pid=pid,
                name=name,
                path=file_path,
                message="Process does not have executable on disk.",
            )
            result.append(alert)
    return result


def detect_process_with_duplicate_name() -> list[Alert]:
    """Checks for two processes that share the same name, but are in different locations on disk.

    NOTE: This could cause false-positives if two different apps contain the same
    helper executable (i.e. JetBrain's fsnotifier)

    :return: A List of Alerts for each process that has no associated executable.
    """
    # import config lazily to avoid circular import when daemon initializes
    from procmond.daemon import config  # noqa: PLC0415

    result = []
    with connect(config.database_path) as conn:
        cur = conn.cursor()
        sql = """
                SELECT id, updated_at, name, path, count(path) AS distinct_paths
                FROM (
                         SELECT id, updated_at, name, path, file_exists
                         FROM processes
                         WHERE updated_at = (SELECT MAX(updated_at) FROM processes)
                           AND accessible = 1
                           AND NOT path ISNULL
                         GROUP BY name, path
                     )
                GROUP BY name
                HAVING distinct_paths > 1
                ORDER BY distinct_paths DESC
                """
        cur.execute(sql)
        for record in cur:
            pid, _updated_at, name, file_path, distinct_paths = record
            alert = Alert(
                pid=pid,
                name=name,
                path=file_path,
                message=(f"{distinct_paths} processes exist with the same name, but different paths."),
            )
            result.append(alert)
    return result


def detect_process_with_hash_change() -> list[Alert]:
    """Checks for processes where the executable on disk has changed while the process is running.

    :return: A List of Alerts for each process that has no associated executable.
    """
    # import config lazily to avoid circular import when daemon initializes
    from procmond.daemon import config  # noqa: PLC0415

    result = []
    with connect(config.database_path) as conn:
        cur = conn.cursor()
        sql = """
                SELECT id, name, path, count(hash) AS unique_hashes
                FROM (
                         SELECT id, updated_at, name, path, hash
                         FROM processes
                         WHERE accessible = 1
                           AND NOT path ISNULL
                           AND NOT hash ISNULL
                         GROUP BY id, path
                         ORDER BY name
                     )
                GROUP BY id, path, hash
                HAVING unique_hashes > 1
                ORDER BY unique_hashes DESC
                """
        cur.execute(sql)
        for record in cur:
            pid, _updated_at, name, file_path, _file_exists = record
            alert = Alert(
                pid=pid,
                name=name,
                path=file_path,
                message=("Process executable has been modified on disk while the process was running."),
            )
            result.append(alert)
    return result
