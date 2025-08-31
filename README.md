# ProcMonD

ProcMonD is a lightweight process tripwire that inspects running processes and their on-disk executables for signs of compromise. It records metadata to a SQLite database and can alert via syslog, email (SMTP), or a configurable HTTP webhook.

## Features

- Detect processes with no corresponding executable on disk
- Detect when an executable on disk changes while the process is running
- Detect multiple processes that share the same name but live at different paths

## Platform compatibility

The codebase is runnable for development on both Linux and Windows, but two modules are POSIX-specific:

- `python-daemon` (daemonization) — intended for Unix systems
- `syslog` (system logging) — available on Unix systems only

Small Windows-safe fallbacks are included so you can test locally on Windows. For production:

- On Linux: run under systemd or another init system and use the real `python-daemon` behavior.
- On Windows: run ProcMonD as a Windows Service (see `docs/windows-service.md`) or use an external service wrapper.

## Quickstart

Recommended Python: 3.10 or newer. Create a virtual environment and install runtime dependencies.

PowerShell (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Bash (Linux / macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

You can pin exact versions for production with the provided `requirements.lock` file:

```bash
pip install -r requirements.lock
```

## Usage

Run in the foreground (useful for debugging):

```bash
python procmond.py
```

By default ProcMonD runs every 30 seconds (configured by `RefreshRate`) and will create a `procmond.db` SQLite database in the configured `RootPath`.

## Configuration

Configuration is INI-format (see `procmond.sample.conf`). Typical locations are `/etc/procmond.conf` or the repo root. Use `--config` to point to a custom config file:

```bash
python procmond.py --config /path/to/procmond.conf
```

Sample alert configuration snippet:

```ini
[ALERT_PROVIDERS]
AlertToEmail = True
AlertToWebHook = True

[EMAIL_CONFIG]
SubjectPrefix = myhost
SMTPServerAddress = smtp.example.com
SMTPServerPort = 587
SenderAddress = root@example.com
DestinationAddress = ops@example.com
UseSSL = False
```

## Deployment

See `docs/systemd.md` for a minimal systemd unit and deployment steps on Linux. See `docs/windows-service.md` for guidance on running as a Windows Service.

### Example systemd unit

```ini
[Unit]
Description=ProcMonD process tripwire
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/procmond
ExecStart=/opt/procmond/.venv/bin/python /opt/procmond/procmond.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

- "No module named 'daemon'": install dependencies into a virtualenv and use `pip install -r requirements.txt` or `requirements.lock`.
- "ModuleNotFoundError: No module named 'pwd'": occurs on Windows because `python-daemon` is POSIX-only. The repo contains a small fallback for Windows testing; for production on Linux install and use `python-daemon`.
- Database write errors: ensure the configured `RootPath` is writable by the user running the service.

## Development & CI

- Add tests for detectors (DB query behavior) and run them in CI.
- Consider adding `pytest`, `flake8`, and a GitHub Actions workflow to run tests and linting on PRs.

## Contributing

Pull requests welcome. For larger changes please open an issue first to discuss the design. Add tests for bug fixes and new features.

## License

This project is licensed under GPLv3.
