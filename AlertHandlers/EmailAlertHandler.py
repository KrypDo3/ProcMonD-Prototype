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
    msg['Subject'] = f"ProcMonD - {config.email_config['subject_prefix']} - Suspicious Process Alerts"
    msg['From'] = config.email_config['sender_address']
    msg['To'] = config.email_config['destination_address']
    msg.set_content(message_text)

    try:
        if config.email_config['smtp_server_use_ssl']:
            s = SMTP_SSL(host=config.email_config['smtp_server_address'], port=config.email_config['smtp_server_port'])
        else:
            s = SMTP(host=config.email_config['smtp_server_address'], port=config.email_config['smtp_server_port'])

        if config.email_config['smtp_server_username'] and config.email_config['smtp_server_password']:
            s.login(user=config.email_config['smtp_server_username'],
                    password=config.email_config['smtp_server_password'])
        s.send_message(msg)
        s.quit()
    except ConnectionRefusedError:
        error("Connection refused to SMTP server.")
    except SMTPAuthenticationError:
        error("SMTP Server refused authentication.")
