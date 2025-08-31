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

try:
    from syslog import LOG_DAEMON, LOG_WARNING, openlog, syslog
except Exception:
    # On non-Unix platforms (Windows) the 'syslog' module is not available.
    # Provide a minimal fallback that logs via the standard logging module.
    import logging

    LOG_DAEMON = None
    LOG_WARNING = logging.WARNING

    def openlog(ident="ProcMonD", facility=None):
        # Configure a logger for fallback syslog behavior.
        logger = logging.getLogger('ProcMonD')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def syslog(level, message):
        logger = logging.getLogger('ProcMonD')
        logger.log(level if isinstance(level, int) else logging.INFO, message)


def syslog_alert_handler(alerts):
    """
    Log each alert to the System Logging facility.
    :param alerts: A List of Alert objects representing each alert to be processed.
    """
    openlog(ident="ProcMonD", facility=LOG_DAEMON)
    for alert in alerts:
        syslog(LOG_WARNING, f"ProcMonD alert: {alert}")
