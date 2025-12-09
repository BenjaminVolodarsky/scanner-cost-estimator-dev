import csv
import os
import json

OUTPUT_DIR = "output"
CSV_FILE = f"{OUTPUT_DIR}/report.csv"


def write_output(data, csv_name="report.csv"):
    """Writes data to CSV and JSON for inspection."""

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # JSON (debug/reference)
    json_path = os.path.join(OUTPUT_DIR, "report.json")
    with open(json_path, "w") as jf:
        json.dump(data, jf, indent=4)
    print(f"JSON saved → {json_path}")

    # Validate CSV data
    if not isinstance(data, list) or len(data) == 0:
        print("No data to write to CSV")
        return

    # Extract header dynamically
    headers = sorted(list(data[0].keys()))

    csv_path = os.path.join(OUTPUT_DIR, csv_name)
    with open(csv_path, "w", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

    print(f"CSV saved → {csv_path}")
