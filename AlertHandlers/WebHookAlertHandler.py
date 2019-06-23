from logging import error

from requests import post

from procmond import config


def webhook_alert_handler(alerts):
    """
    Sends a message to a web server containing each alert via HTTP POST.
    :param alerts: A List of Alert objects representing each alert to be processed.
    """
    message_text = ""
    for alert in alerts:
        message_text += f"{alert}\n"
    data = {'text': message_text}
    response = post(config.webhook_address, json=data)
    if response.status_code != 200:
        error(f'Request to webhook returned an error {response.status_code}, the response is:\n\t{response.text}')
