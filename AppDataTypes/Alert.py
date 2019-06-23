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

class Alert:
    """
    The Alert class encapsulates the metadata for a suspicious event.
    """
    message: str
    path: str
    name: str
    pid: int

    def __init__(self, pid=0, name="", path="", message=""):
        """
        Creates a new Alert object that represents a detected suspicious event.
        :param pid: The ID of the suspicious process.
        :param name: The name of the process, as it appears in ps.
        :param path: The path on disk of the process's executable file.
        :param message: The alert message explaining the suspicious activity.
        """
        self.pid = pid
        self.name = name
        self.path = path
        self.message = message

    def __str__(self):
        return f"{self.name}({self.pid}) {self.message}"
