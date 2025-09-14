"""Tiny smoke test: run a single pass of the lightweight functions (no daemon loop)."""

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton
from procmond.daemon import check_alerts, get_processes

if __name__ == "__main__":
    processes = get_processes()
    print(f"Found {len(processes)} processes")
    for p in processes[:5]:
        try:
            print(p.to_dict)
        except (AttributeError, TypeError) as e:
            print("Error serializing process:", e)
    alerts = check_alerts()
    print(f"Found {len(alerts)} alerts")
    for a in alerts[:5]:
        print(a)
