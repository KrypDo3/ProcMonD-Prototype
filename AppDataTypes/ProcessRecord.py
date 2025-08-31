#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
#  Copyright (C) 2019  Krystal Melton
#
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
#  details.
#
#  You should have received a copy of the GNU General Public License along with this program.  If not,
#  see <https://www.gnu.org/licenses/>.
#

from __future__ import annotations

from hashlib import sha256
from logging import error, warning
from pathlib import Path
from typing import Dict


class ProcessRecord:
    """
    The ProcessRecord class encapsulates the metadata for an individual running process.
    """

    pid: int
    ppid: int
    file_path: str
    name: str
    valid: bool
    accessible: bool

    def __init__(self, pid: int) -> None:
        """
        Creates a new ProcessRecord to encapsulate the metadata for an individual running process.
        :type pid: The ID of the process
        """
        self.name = ""
        self.__path = ""
        self.pid = pid
        self.ppid = 0
        self.valid = False
        self.accessible = False
        self.__path = ""

    @property
    def to_dict(self) -> Dict[str, object]:
        """

        :return:
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
        """

        :return:
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
        """

        :return:
        """
        file_hash = ""
        if not self.exists:
            return file_hash
        try:
            # lazily import config to avoid circular imports; fall back to a sensible default
            try:
                import sys

                pm = sys.modules.get("procmond")
                if pm is not None and hasattr(pm, "config"):
                    _config = pm.config
                    _buf = getattr(_config, "hash_buffer_size", 1024)
                else:
                    _buf = 1024
            except Exception:
                _buf = 1024

            with open(self.path, "rb") as f:
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
            warning(
                f"{self.name} ({self.pid}) executable file exists, but we don't have access."
            )
            self.accessible = False
            self.valid = True
        finally:
            return file_hash

    @property
    def exists(self) -> bool:
        """

        :return:
        """
        if not self.path:
            return False
        try:
            return Path(self.path).exists()
        except PermissionError:
            self.accessible = False
            error(
                f"Process '{self.name} executable file exists, but we don't have access."
            )
            return False

    def __str__(self) -> str:
        return f"{self.name} ({self.pid})"
