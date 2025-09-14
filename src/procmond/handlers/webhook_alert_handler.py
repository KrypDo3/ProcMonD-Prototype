"""Webhook alert handler for ProcMonD.

This module provides functionality to send alerts to a webhook endpoint
when suspicious process behavior is detected.
"""

#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from requests import post

if TYPE_CHECKING:
    from collections.abc import Iterable

    from procmond.models.alert import Alert

from procmond.daemon import config

logger = getLogger(__name__)

# HTTP status code constants
HTTP_OK = 200


def webhook_alert_handler(alerts: Iterable[Alert]) -> None:
    """Sends a message to a web server containing each alert via HTTP POST.

    :param alerts: A List of Alert objects representing each alert to be processed.
    """
    message_text = ""
    for alert in alerts:
        message_text += f"{alert}\n"
    data = {"text": message_text}
    # include a short timeout to avoid blocking the daemon
    response = post(config.webhook_address, json=data, timeout=5)
    if response.status_code != HTTP_OK:
        logger.error(
            "Request to webhook returned an error %s, the response is:\n\t%s",
            response.status_code,
            response.text,
        )
