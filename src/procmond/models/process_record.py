"""Process record model for ProcMonD.

This module defines the ProcessRecord class which encapsulates metadata
for individual running processes.
"""

#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton

from __future__ import annotations

import sys
from hashlib import sha256
from logging import getLogger
from pathlib import Path
from typing import Any

logger = getLogger(__name__)


class ProcessRecord:
    """The ProcessRecord class encapsulates the metadata for an individual running process."""

    pid: int
    ppid: int
    file_path: str
    name: str
    valid: bool
    accessible: bool

    def __init__(self, pid: int) -> None:
        """Creates a new ProcessRecord to encapsulate the metadata for an individual running process.

        :param pid: The ID of the process.
        """
        self.name = ""
        self.__path = ""
        self.pid = pid
        self.ppid = 0
        self.valid = False
        self.accessible = False
        self.__path = ""

    @property
    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the process record.

        :return: A dictionary containing all process record fields.
        """
        return {
            "pid": self.pid,
            "ppid": self.ppid,
            "name": self.name,
            "path": self.path,
            "hash": self.hash,
            "exists": self.exists,
            "valid": self.valid,
            "accessible": self.accessible,
        }

    @property
    def path(self) -> str:
        """Get the process executable path.

        :return: The path to the process executable.
        """
        return self.__path

    @path.setter
    def path(self, file_path: str) -> None:
        if file_path == "/" or not file_path:
            self.valid = False
        else:
            self.valid = True
        self.__path = file_path

    @property
    def hash(self) -> str:
        """Calculate and return the SHA256 hash of the process executable.

        :return: The SHA256 hash of the process executable file.
        """
        file_hash = ""
        if not self.exists:
            return file_hash
        try:
            # lazily import config to avoid circular imports; fall back to a sensible default
            try:
                pm = sys.modules.get("procmond")
                if pm is not None and hasattr(pm, "config"):
                    _config = pm.config
                    _buf = getattr(_config, "hash_buffer_size", 1024)
                else:
                    _buf = 1024
            except (ImportError, AttributeError):
                _buf = 1024

            with Path(self.path).open("rb") as f:
                hasher = sha256()
                r = f.read(_buf)
                while r:
                    hasher.update(r)
                    r = f.read(_buf)
                file_hash = hasher.hexdigest()
                self.valid = True
                self.accessible = True
        except IsADirectoryError:
            if self.path == "/":
                self.valid = False
            self.accessible = False
        except PermissionError:
            logger.warning(
                "%s (%s) executable file exists, but we don't have access.",
                self.name,
                self.pid,
            )
            self.accessible = False
            self.valid = True
        return file_hash

    @property
    def exists(self) -> bool:
        """Check if the process executable file exists on disk.

        :return: True if the file exists, False otherwise.
        """
        if not self.path:
            return False
        try:
            return Path(self.path).exists()
        except PermissionError:
            self.accessible = False
            logger.exception(
                "Process '%s' executable file exists, but we don't have access.",
                self.name,
            )
            return False

    def __str__(self) -> str:
        """Return a string representation of the process record.

        :return: A string representation of the process record.
        """
        return f"{self.name} ({self.pid})"
