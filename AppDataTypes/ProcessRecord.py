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

from hashlib import sha256
from logging import error, warning
from pathlib import Path

import procmond


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

    def __init__(self, pid):
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
    def to_dict(self):
        """

        :return:
        """
        return {'pid':        self.pid,
                'ppid':       self.ppid,
                'name':       self.name,
                'path':       self.path,
                'hash':       self.hash,
                'exists':     self.exists,
                'valid':      self.valid,
                'accessible': self.accessible
                }

    @property
    def path(self):
        """

        :return:
        """
        return self.__path

    @path.setter
    def path(self, file_path):
        if file_path == "/" or not file_path:
            self.valid = False
        else:
            self.valid = True
        self.__path = file_path

    @property
    def hash(self):
        """

        :return:
        """
        file_hash = ""
        if not self.exists:
            return file_hash
        try:
            with open(self.path, "rb") as f:
                hasher = sha256()
                r = f.read(procmond.config.hash_buffer_size)
                while r:
                    hasher.update(r)
                    r = f.read(procmond.config.hash_buffer_size)
                file_hash = hasher.hexdigest()
                self.valid = True
                self.accessible = True
        except IsADirectoryError:
            if self.path == "/":
                self.valid = False
            self.accessible = False
        except PermissionError:
            warning(f"{self.name} ({self.pid}) executable file exists, but we don't have access.")
            self.accessible = False
            self.valid = True
        finally:
            return file_hash

    @property
    def exists(self):
        """

        :return:
        """
        if not self.path:
            return False
        try:
            return Path(self.path).exists()
        except PermissionError:
            self.accessible = False
            error(f"Process '{self.name} executable file exists, but we don't have access.")
            return False

    def __str__(self):
        return f"{self.name} ({self.pid})"
