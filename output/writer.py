import json
import csv
import os

def write_output(data, csv_name="report.csv"):
    os.makedirs("output", exist_ok=True)

    # Save JSON (raw)
    with open("output/report.json", "w") as f:
        json.dump(data, f, indent=2)
    print("JSON saved → output/report.json")

    # -------- CSV FIX HERE --------
    # Collect all keys across all records
    fieldnames = set()
    for item in data:
        fieldnames.update(item.keys())

    fieldnames = sorted(fieldnames)   # nice consistent order

    # Write CSV with dynamic columns
    csv_path = f"output/{csv_name}"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"CSV saved → {csv_path}")
