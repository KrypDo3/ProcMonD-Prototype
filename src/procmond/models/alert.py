"""Alert model for ProcMonD.

This module defines the Alert class which represents a detected
suspicious process event.
"""

#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton

from __future__ import annotations


class Alert:
    """The Alert class encapsulates the metadata for a suspicious event."""

    message: str
    path: str
    name: str
    pid: int

    def __init__(self, pid: int = 0, name: str = "", path: str = "", message: str = "") -> None:
        """Creates a new Alert object that represents a detected suspicious event.

        :param pid: The ID of the suspicious process.
        :param name: The name of the process, as it appears in ps.
        :param path: The path on disk of the process's executable file.
        :param message: The alert message explaining the suspicious activity.
        """
        self.pid = pid
        self.name = name
        self.path = path
        self.message = message

    def __str__(self) -> str:
        """Return a string representation of the alert.

        :return: A string representation of the alert.
        """
        return f"{self.name}({self.pid}) {self.message}"
