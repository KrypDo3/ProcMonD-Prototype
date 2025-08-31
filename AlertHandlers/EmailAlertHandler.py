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

from email.message import EmailMessage
from logging import error
from smtplib import SMTP, SMTP_SSL, SMTPAuthenticationError

from procmond import config


def email_alert_handler(alerts):
    """
    Sends an email containing each alert via an SMTP server.
    :param alerts: A List of Alert objects representing each alert to be processed.
    """
    message_text = ""
    for alert in alerts:
        message_text += f"{alert}\n"
    msg = EmailMessage()
    msg["Subject"] = (
        f"ProcMonD - {config.email_config['subject_prefix']} - Suspicious Process Alerts"
    )
    msg["From"] = config.email_config["sender_address"]
    msg["To"] = config.email_config["destination_address"]
    msg.set_content(message_text)

    try:
        if config.email_config["smtp_server_use_ssl"]:
            s = SMTP_SSL(
                host=config.email_config["smtp_server_address"],
                port=config.email_config["smtp_server_port"],
            )
        else:
            s = SMTP(
                host=config.email_config["smtp_server_address"],
                port=config.email_config["smtp_server_port"],
            )

        if (
            config.email_config["smtp_server_username"]
            and config.email_config["smtp_server_password"]
        ):
            s.login(
                user=config.email_config["smtp_server_username"],
                password=config.email_config["smtp_server_password"],
            )
        s.send_message(msg)
        s.quit()
    except ConnectionRefusedError:
        error("Connection refused to SMTP server.")
    except SMTPAuthenticationError:
        error("SMTP Server refused authentication.")
