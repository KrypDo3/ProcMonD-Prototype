# Running ProcMonD as a Windows Service

This document explains two practical ways to run ProcMonD as a managed service on Windows: (A) using NSSM (the Non-Sucking Service Manager) for a quick, production-ready wrapper, and (B) implementing a native Windows Service with `pywin32` if you prefer a pure-Python service. It also explains caveats you must know about running ProcMonD on Windows.

IMPORTANT CAVEAT — LIKELY FALSE POSITIVES ON WINDOWS

ProcMonD's detection logic was originally designed for Unix-like systems and inspects process metadata and on-disk executables. On Windows, process/executable behavior differs (system processes, permission models, file-locking, service helper processes, and multiple executables with identical names in different system paths). As a result, you should expect higher rates of false positives when running ProcMonD on Windows. Use these deployments for monitoring and testing, but carefully tune alerting thresholds and exclusion lists before relying on the results for automated incident response.

Prerequisites

- Windows machine with admin privileges for service install
- Python 3.10+ and a virtualenv for ProcMonD
- ProcMonD code copied to a stable path (for example: `C:\opt\procmond`)

General advice

- Run ProcMonD under a dedicated service account with minimal privileges.
- Use the repository's virtualenv to isolate dependencies.
- Use `requirements.lock` for reproducible installs in production.
- Tune `procmond.conf` to exclude known benign paths/processes to reduce false positives.

Option A — Quick: install with NSSM (recommended for simplicity)

1. Download and install NSSM from the project site and place `nssm.exe` on PATH or a known folder. See: [NSSM](https://nssm.cc/)

2. Prepare the application folder and virtualenv (example):

```powershell
mkdir C:\opt\procmond
cd C:\opt\procmond
# copy the repo contents here
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock
```

1. Install the service (run an elevated PowerShell):

```powershell
nssm install ProcMonD C:\opt\procmond\.venv\Scripts\python.exe C:\opt\procmond\procmond.py
nssm set ProcMonD AppDirectory C:\opt\procmond
nssm set ProcMonD Start SERVICE_AUTO_START
nssm set ProcMonD AppStdout C:\opt\procmond\procmond.log
nssm set ProcMonD AppStderr C:\opt\procmond\procmond.err.log
nssm start ProcMonD
```

1. Manage the service with the Services MMC or via `nssm` / `sc` / `net` commands.

Notes for NSSM

- NSSM is a wrapper that runs the Python program as a Windows service. It does not convert any Unix-only functionality — the repo contains Windows-safe fallbacks for daemonization and syslog.
- Logs written by ProcMonD will go to the configured log files; also check the Windows Event Log for NSSM service events.

Option B — Native Python Windows Service (pywin32)

If you prefer a native service, use `pywin32` to register a Windows Service that launches ProcMonD. This approach requires more code but integrates with Windows Service Control Manager (SCM).

1. Install pywin32 in your virtualenv:

```powershell
pip install pywin32
```

1. Minimal service wrapper (place as `service_runner.py` in the repo):

```python
import servicemanager
import win32serviceutil
import win32service
import win32event
import subprocess
import sys


class ProcMonDService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ProcMonD"
    _svc_display_name_ = "ProcMonD process tripwire"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.proc = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.proc:
            self.proc.terminate()
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        # Launch ProcMonD under the active virtualenv Python
        python = r"C:\opt\procmond\.venv\Scripts\python.exe"
        self.proc = subprocess.Popen(
            [python, r"C:\opt\procmond\procmond.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, 0, ("ProcMonD service started", ""))
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(ProcMonDService)
```

1. Install the service (run elevated PowerShell):

```powershell
cd C:\opt\procmond
.\.venv\Scripts\python.exe service_runner.py install
.\.venv\Scripts\python.exe service_runner.py start
```

1. Stop / remove the service:

```powershell
.\.venv\Scripts\python.exe service_runner.py stop
.\.venv\Scripts\python.exe service_runner.py remove
```

Notes for pywin32 approach

- If ProcMonD writes logs to files, ensure the service account can write to them.
- Use SCM or Event Viewer to inspect service events and startup failures.

Alternative — Task Scheduler (less integrated)

You can also run ProcMonD at startup via Task Scheduler (set to run as a user with highest privileges). This is simpler but lacks the full service control integration.

Permissions and tuning

- Create an exclusion list in your `procmond.conf` for known Windows helpers (e.g., `System Idle Process`, `Registry` helpers, or vendor update services) to reduce false positives.
- Ensure the service account can read process/executable metadata and write the SQLite DB.

Troubleshooting

- "ModuleNotFoundError: No module named 'pwd'": expected on Windows — this repo includes a fallback for testing. No action required unless you want Unix daemon behavior.
- High false positive rate: tune exclusions and confirm the `RootPath` and `HashBufferSize` settings in the config.
- Service fails to start: check service logs, `procmond.err.log` (if using NSSM), and the Windows Event Log.

Further reading

- Linux deployment: `docs/systemd.md`
- Repository README: `README.md`
