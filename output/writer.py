import json
import csv
import os

def write_output(data, json_name="upwind_report.json", csv_name="upwind_report.csv"):
    os.makedirs("output", exist_ok=True)

    # Save JSON
    with open(f"output/{json_name}", "w") as jf:
        json.dump(data, jf, indent=2)

    # Get all unique fields for CSV header
    fieldnames = sorted({k for item in data for k in item.keys()})

    # Save CSV
    with open(f"output/{csv_name}", "w", newline='') as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"\nJSON saved → output/{json_name}")
    print(f"CSV saved  → output/{csv_name}")
