"""Syslog alert handler for ProcMonD.

This module provides functionality to send alerts to the system logging
facility when suspicious process behavior is detected.
"""

#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton

from collections.abc import Iterable

try:
    import syslog as _syslog_mod

    LOG_DAEMON = getattr(_syslog_mod, "LOG_DAEMON", None)
    LOG_WARNING = getattr(_syslog_mod, "LOG_WARNING", None)

    def openlog(ident: str = "ProcMonD", facility: int | None = None) -> None:
        """Configure syslog with the given identifier and facility."""
        _syslog_mod.openlog(ident, facility=facility or 0)

    def syslog(level: int, message: str) -> None:
        """Log a message at the specified level."""
        _syslog_mod.syslog(level, message)
except ImportError:
    # On non-Unix platforms (Windows) the 'syslog' module is not available.
    # Provide a minimal fallback that logs via the standard logging module.
    import logging

    LOG_DAEMON_FALLBACK: int | None = None
    LOG_WARNING_FALLBACK: int = logging.WARNING

    def openlog(ident: str = "ProcMonD", facility: int | None = None) -> None:  # noqa: ARG001, unused-parameter  # type: ignore[unused-parameter]
        """Configure a logger for fallback syslog behavior.

        :param ident: The identifier for the logger.
        :param facility: The syslog facility (unused in fallback).
        """
        logger = logging.getLogger("ProcMonD")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def syslog(level: int, message: str) -> None:
        """Log a message at the specified level.

        :param level: The log level.
        :param message: The message to log.
        """
        logger = logging.getLogger("ProcMonD")
        logger.log(level, message)


def syslog_alert_handler(alerts: Iterable[object]) -> None:
    """Log each alert to the System Logging facility.

    :param alerts: A List of Alert objects representing each alert to be processed.
    """
    openlog(ident="ProcMonD", facility=LOG_DAEMON_FALLBACK)
    for alert in alerts:
        syslog(LOG_WARNING_FALLBACK, f"ProcMonD alert: {alert}")
