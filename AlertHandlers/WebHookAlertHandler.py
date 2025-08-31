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

from logging import error
from typing import Iterable

from requests import post

from procmond import config


def webhook_alert_handler(alerts: Iterable[object]) -> None:
    """
    Sends a message to a web server containing each alert via HTTP POST.
    :param alerts: A List of Alert objects representing each alert to be processed.
    """
    message_text = ""
    for alert in alerts:
        message_text += f"{alert}\n"
    data = {"text": message_text}
    # include a short timeout to avoid blocking the daemon
    response = post(config.webhook_address, json=data, timeout=5)
    if response.status_code != 200:
        error(
            f"Request to webhook returned an error {response.status_code}, the response is:\n\t{response.text}"
        )
