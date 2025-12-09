import json
import os

def write_output(data, filename="cloudscanner_cost_data.json"):
    os.makedirs("output", exist_ok=True)

    with open(f"output/{filename}", "w") as f:
        json.dump(data, f, indent=2)
