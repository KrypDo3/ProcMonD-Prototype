# Tiny smoke test: run a single pass of the lightweight functions (no daemon loop)
from procmond import check_alerts, get_processes

if __name__ == "__main__":
    processes = get_processes()
    print(f"Found {len(processes)} processes")
    for p in processes[:5]:
        try:
            print(p.to_dict)
        except Exception as e:
            print("Error serializing process:", e)
    alerts = check_alerts()
    print(f"Found {len(alerts)} alerts")
    for a in alerts[:5]:
        print(a)
