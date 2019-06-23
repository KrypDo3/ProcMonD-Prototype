# ProcMonD

ProcMonD is a process tripwire that runs as a daemon, monitors the processes in memory, and their corresponding executables on disk, for indications of malicious activity. It will go through the processes currently in memory, locate the associated executable on disk, and write the metadata to a database. 

This will find three indication of malicious activity: 
- Processes with no corresponding executables on disk
- Processes where the executable has changed while the process is running
- Multiple processes that share the same name, but are in different locations on disk.

ProcMonD currently supports multiple alerting mechanism, including:
- Write to syslog
- Email via a configured SMTP server
- Triggering a user-configurable webhook

### Prototype Note
While feature-complete, this version of the project was written for a Python Security class I took. I intend to rewrite this project in Go for the production version. You are welcome to use this version, but all development focus will be on the Go version. When completed, it will be available under the same licence via GitHub.

## Installation

ProcMonD requires Python 3 (preferably 3.7 or higher). 

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the required supporting modules.

```bash
pip3 install -r requirements.txt
```

## Usage

```bash
python3 procmond.py
```

When started, ProcMonD runs every 30 seconds, or the value specified in the procmond.conf file with the RefreshRate parameter, and automatically creates a sqlite3 database in the project's RootPath (/var/lib/procmond by default) to store the process information.

## Configuration
ProcMonD uses a standard ini-formatted configuration file that is typically located either in /etc/procmond.conf or in the same directory as the code.

To provide an alternate configuration file, procmond.py can be started with the --config parameter. For example:
```bash
procmond.py --config /home/procmond/procmond.config
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)