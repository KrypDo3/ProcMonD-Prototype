# Deploying ProcMonD with systemd (Linux)

This document shows a minimal, practical way to run ProcMonD as a managed system service with systemd.

Prerequisites

- A Linux host with systemd
- Python 3.10+ installed
- A virtual environment for ProcMonD (recommended)
- `requirements.lock` or `requirements.txt` available in the project directory

Steps

1. Prepare an application user (optional but recommended):

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin procmond
sudo mkdir -p /opt/procmond
sudo chown procmond:procmond /opt/procmond
```

1. Copy the project to the target directory and create a virtualenv (run as deploy user):

```bash
sudo -u procmond -H bash -c '
  cp -r /path/to/ProcMonD-Prototype/* /opt/procmond/
  python3 -m venv /opt/procmond/.venv
  source /opt/procmond/.venv/bin/activate
  pip install --upgrade pip
  pip install -r /opt/procmond/requirements.lock
'
```

1. Create a systemd unit file `/etc/systemd/system/procmond.service` with contents similar to:

```ini
[Unit]
Description=ProcMonD process tripwire
After=network.target

[Service]
Type=simple
User=procmond
Group=procmond
WorkingDirectory=/opt/procmond
Environment=PATH=/opt/procmond/.venv/bin:/usr/bin:/bin
ExecStart=/opt/procmond/.venv/bin/python /opt/procmond/procmond.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Notes:

- `User`/`Group`: run the service as a non-root user with minimal permissions.
- `Environment=PATH=...` ensures the venv Python is used; an alternative is to use an `EnvironmentFile` with vars.

1. Reload systemd and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now procmond.service
```

1. Check service status and logs:

```bash
sudo systemctl status procmond.service
sudo journalctl -u procmond.service -f
```

Troubleshooting

- If ProcMonD cannot write to the database, check the `RootPath` setting and filesystem permissions for the service user.
- If using SELinux, ensure the service user and file locations have appropriate contexts or create a policy module.

Security and production notes

- Use `requirements.lock` to pin exact runtime dependencies in production.
- Consider running ProcMonD inside a container or with additional sandboxing if you monitor untrusted systems.
