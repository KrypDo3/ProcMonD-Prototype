"""Email alert handler for ProcMonD.

This module provides functionality to send email alerts when suspicious
process behavior is detected.
"""

#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton

from __future__ import annotations

from email.message import EmailMessage
from logging import getLogger
from smtplib import SMTP, SMTP_SSL, SMTPAuthenticationError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from procmond.models.alert import Alert

from procmond.daemon import config

logger = getLogger(__name__)


def email_alert_handler(alerts: Iterable[Alert]) -> None:
    """Sends an email containing each alert via an SMTP server.

    :param alerts: A List of Alert objects representing each alert to be processed.
    """
    message_text = ""
    for alert in alerts:
        message_text += f"{alert}\n"
    msg = EmailMessage()
    msg["Subject"] = f"ProcMonD - {config.email_config['subject_prefix']} - Suspicious Process Alerts"
    msg["From"] = config.email_config["sender_address"]
    msg["To"] = config.email_config["destination_address"]
    msg.set_content(message_text)

    try:
        if config.email_config["smtp_server_use_ssl"]:
            s = SMTP_SSL(
                host=str(config.email_config["smtp_server_address"]),
                port=int(config.email_config["smtp_server_port"]),
            )
        else:
            s = SMTP(
                host=str(config.email_config["smtp_server_address"]),
                port=int(config.email_config["smtp_server_port"]),
            )

        if config.email_config["smtp_server_username"] and config.email_config["smtp_server_password"]:
            s.login(
                user=str(config.email_config["smtp_server_username"]),
                password=str(config.email_config["smtp_server_password"]),
            )
        s.send_message(msg)
        s.quit()
    except ConnectionRefusedError:
        logger.exception("Connection refused to SMTP server.")
    except SMTPAuthenticationError:
        logger.exception("SMTP Server refused authentication.")
