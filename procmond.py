# !/usr/bin/env python3

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

from datetime import datetime
from logging import basicConfig, debug, fatal, info, warning
from sqlite3 import connect, OperationalError
from time import sleep

from daemon import DaemonContext
from psutil import AccessDenied, process_iter, ZombieProcess

import Detectors
from AppDataTypes.ProcessRecord import ProcessRecord
from ConfigManager import ConfigManager

config = ConfigManager()
daemon_ctx = DaemonContext()


def main():
    """
    The main function that is run when the process monitoring daemon starts up.
    """
    global daemon_ctx

    basicConfig(format=config.log_message_format, datefmt=config.log_message_datefmt,
                level=config.numeric_log_level)
    with open(config.log_file, "w") as out_log:
        daemon_ctx.detach_process = False
        daemon_ctx.stderr = out_log
        daemon_ctx.working_directory = config.root_path
        with daemon_ctx:
            info("ProcMonD monitoring service starting up.")
            info(f"Storing in database: {config.database_path}")
            if config.alert_to_syslog:
                info("Logging to syslog")
            if config.alert_to_email:
                info("Logging to email")
            if config.alert_to_webhook:
                info("Logging to webhook")

            try:
                while True:
                    debug("Performing process checks.")
                    process_records = get_processes()
                    store_records(process_records)
                    alerts = check_alerts()
                    if alerts:
                        action_alerts(alerts)

                    sleep(config.refresh_rate)
            except KeyboardInterrupt:
                daemon_ctx.close()
                quit(-1)


def get_processes():
    """
    Walks the current process list and returns a List of ProcessRecord objects containing the process information.
    :return: The collection of process records.
    """
    process_records = []
    for process in process_iter():
        proc = ProcessRecord(process.pid)
        try:
            proc.name = process.name()
            proc.ppid = process.ppid()
            proc.path = process.exe()

        except AccessDenied:
            warning(f"{proc} is not an accessible process.")
            proc.valid = False
        except FileNotFoundError:
            warning(f"{proc} executable could not be found.")
            proc.valid = True
            proc.accessible = True
        except ZombieProcess:
            warning(f"{proc} is a zombie process.")
            proc.valid = False
        finally:
            if proc.valid is True:
                process_records.append(proc)

    return process_records


def store_records(process_records):
    """
    Stores a List of ProcessRecord objects in a SQLite3 database.
    :param process_records: A List of ProcessRecords representing each process identified.
    """
    try:
        with connect(config.database_path) as conn:
            cur = conn.cursor()
            # Create the database if it doesn't already exist.
            cur.execute(
                'CREATE TABLE IF NOT EXISTS processes '
                '(id INTEGER, ppid INTEGER, updated_at DATETIME, name VARCHAR, path VARCHAR, '
                'valid BIT, "hash" VARCHAR, accessible BIT, file_exists BIT, '
                'CONSTRAINT processes_pk PRIMARY KEY (id, updated_at));'
            )
            cur.execute('CREATE INDEX IF NOT EXISTS processes_name_hash_index ON processes (name DESC, hash DESC);')
            cur.execute('CREATE INDEX IF NOT EXISTS processes_updated_at_index ON processes(updated_at DESC);')
            cur.execute(
                'CREATE INDEX IF NOT EXISTS processes_file_exists_accessible_updated_at_index ON processes ('
                'file_exists, '
                'accessible, updated_at);')
            cur.execute("CREATE INDEX IF NOT EXISTS processes_id_path_hash_index ON processes (id, path, hash);")
            conn.commit()

            # Now insert the new record.
            timestamp = datetime.now()
            insert_sql = "INSERT INTO processes (id, ppid, updated_at, name , path , valid , hash , accessible, " \
                         "file_exists) " \
                         "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            for p in process_records:
                if p.valid:
                    cur.execute(insert_sql, (p.pid,
                                             p.ppid,
                                             timestamp,
                                             p.name,
                                             p.path,
                                             p.valid,
                                             p.hash,
                                             p.accessible,
                                             p.exists)
                                )
            conn.commit()
    except OperationalError:
        fatal(f"Cannot write to database file {config.database_path}")
        daemon_ctx.close()
        quit(-1)


def check_alerts():
    """
    Runs each alert test to see if anything is amiss. If it is, it adds an Alert to the alerts List.
    :return: A List of alerts.
    """
    alerts = []

    alerts.extend(Detectors.detect_process_without_exe())
    alerts.extend(Detectors.detect_process_with_hash_change())
    alerts.extend(Detectors.detect_process_with_duplicate_name())
    return alerts


def action_alerts(alerts):
    """
    Triggers each enabled action type on the list of Alerts.
    :param alerts: A List of Alert objects representing each alert to be processed.
    """
    if config.alert_to_syslog:
        from AlertHandlers.SyslogAlertHandler import syslog_alert_handler
        syslog_alert_handler(alerts)

    if config.alert_to_email:
        from AlertHandlers.EmailAlertHandler import email_alert_handler
        email_alert_handler(alerts)

    if config.alert_to_webhook:
        from AlertHandlers.WebHookAlertHandler import webhook_alert_handler
        webhook_alert_handler(alerts)


if __name__ == "__main__":
    main()
