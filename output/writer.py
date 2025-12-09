import json
import csv
import os

def write_output(data, json_filename="output.json", csv_filename="output.csv"):
    os.makedirs("output", exist_ok=True)

    # JSON
    with open(f"output/{json_filename}", "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nJSON saved → output/{json_filename}")

    # CSV
    if len(data) > 0:
        keys = set()
        for row in data:
            keys.update(row.keys())

        with open(f"output/{csv_filename}", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(keys))
            writer.writeheader()
            writer.writerows(data)

        print(f"CSV saved  → output/{csv_filename}")
