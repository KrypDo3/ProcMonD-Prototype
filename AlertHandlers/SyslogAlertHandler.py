from syslog import LOG_DAEMON, LOG_WARNING, openlog, syslog


def syslog_alert_handler(alerts):
    """
    Log each alert to the System Logging facility.
    :param alerts: A List of Alert objects representing each alert to be processed.
    """
    openlog(ident="ProcMonD", facility=LOG_DAEMON)
    for alert in alerts:
        syslog(LOG_WARNING, f"ProcMonD alert: {alert}")
