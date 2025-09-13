"""Configuration management for ProcMonD.

This module handles loading and managing configuration settings
from INI files and command line arguments.
"""

#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton

import logging
from argparse import ArgumentParser
from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from socket import gethostname
from typing import ClassVar


def get_system_hostname() -> str:
    """Gets the local system's hostname.

    :return: The local hostname.
    """
    return gethostname()


def get_custom_config_path() -> str:
    """Get a user provided configuration file path from command line arguments.

    :return: Any user-provided config file location.
    """
    parser = ArgumentParser()
    parser.add_argument("--config", help="an alternate config file.")
    # Use parse_known_args so test runners (pytest) or other wrappers with extra args
    # don't cause an immediate SystemExit on unknown arguments.
    args, _ = parser.parse_known_args()
    return args.config


class ConfigManager:
    """The ConfigManager handles setting up configuration defaults and loading the application's configuration from an INI-format file."""  # noqa: E501

    root_path: str | Path = Path.cwd()
    database_path: str = "procmond.db"
    refresh_rate: int = 30
    hash_buffer_size: int = 1024
    alert_to_syslog: bool = True
    alert_to_email: bool = False
    alert_to_webhook: bool = False
    email_config: ClassVar[dict[str, str | int | bool]] = {}
    logging_level: str = "INFO"
    log_file: str = "procmond.log"
    log_message_format: str = "%(asctime)s [%(levelname)s]: %(message)s"
    log_message_datefmt: str = "%m/%d/%Y %I:%M:%S %p"

    def __init__(self) -> None:
        """Loads the application configuration from the config file."""
        user_config_path = get_custom_config_path()

        config = ConfigParser(interpolation=ExtendedInterpolation())
        config["GENERAL"] = {}  # Creating an empty section to enable defaults.
        config["ALERT_PROVIDERS"] = {}  # Creating an empty section to enable defaults.
        config_locations = ["/etc/procmond.conf", "procmond.conf"]
        if user_config_path:
            config_locations = user_config_path
        config.read(config_locations)

        self.root_path = config["GENERAL"].get("RootPath", self.root_path)
        self.database_path = config["GENERAL"].get("DatabasePath", self.database_path)
        self.refresh_rate = config["GENERAL"].getint("RefreshRate", self.refresh_rate)
        self.hash_buffer_size = config["GENERAL"].getint("HashBufferSize", self.hash_buffer_size)
        self.logging_level = config["GENERAL"].get("ApplicationLoggingLevel", self.logging_level)
        self.log_file = config["GENERAL"].get("LogFile", self.log_file)

        self.alert_to_syslog = config["ALERT_PROVIDERS"].getboolean("AlertToSyslog", self.alert_to_syslog)
        self.alert_to_email = config["ALERT_PROVIDERS"].getboolean("AlertToEmail", self.alert_to_email)
        self.alert_to_webhook = config["ALERT_PROVIDERS"].getboolean("AlertToWebHook", self.alert_to_webhook)

        if self.alert_to_email and config.has_section("EMAIL_CONFIG"):
            email_section = config["EMAIL_CONFIG"]
            self.email_config["subject_prefix"] = email_section.get("SubjectPrefix", get_system_hostname())
            self.email_config["smtp_server_address"] = email_section.get("SMTPServerAddress", "localhost")
            self.email_config["smtp_server_port"] = email_section.getint("SMTPServerPort", 25)
            self.email_config["smtp_server_username"] = email_section.get("SMTPServerUsername", "")
            self.email_config["smtp_server_password"] = email_section.get("SMTPServerPassword", "")
            self.email_config["sender_address"] = email_section.get("SenderAddress", "root@localhost")
            self.email_config["destination_address"] = email_section.get("DestinationAddress", "root@localhost")
            self.email_config["smtp_server_use_ssl"] = email_section.getboolean("UseSSL", False)
        if self.alert_to_webhook and config.has_section("WEBHOOK_CONFIG"):
            webhook_section = config["WEBHOOK_CONFIG"]
            self.webhook_address = webhook_section.get("EndpointURL", "")

    @property
    def numeric_log_level(self) -> int:
        """Provides the configured logging level as an integer for use in the logging package."""
        numeric_level = getattr(logging, self.logging_level.upper(), None)
        if not isinstance(numeric_level, int):
            msg = f"Invalid log level: {self.logging_level}"
            raise TypeError(msg)
        return numeric_level
