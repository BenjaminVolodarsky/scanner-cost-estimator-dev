import json
import csv
import os


def write_output(data, json_filename="output.json", csv_filename="output.csv"):
    os.makedirs("output", exist_ok=True)

    # 1. Always save JSON
    with open(f"output/{json_filename}", "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n✅ JSON saved → output/{json_filename}")

    # 2. Handle CSV logic
    if not data:
        print("⚠️ No data collected; skipping CSV generation.")
        return

    # Extract all unique keys for headers
    keys = set()
    for row in data:
        keys.update(row.keys())

    # Ensure account_id and resource are the first columns for readability
    fieldnames = sorted(list(keys))
    if "account_id" in fieldnames:
        fieldnames.insert(0, fieldnames.pop(fieldnames.index("account_id")))

    with open(f"output/{csv_filename}", "w", newline="") as f:
        # Use DictWriter to map dictionaries to rows
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ CSV saved  → output/{csv_filename}")