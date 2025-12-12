"""Check if leads.json has nested structure."""
import json
from pathlib import Path


def check_structure(file_path):
    """Analyze JSON structure to find nesting issues."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {file_path}: {e}")
        return

    print(f"File: {file_path}")
    print(f"Type: {type(data)}")

    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        if "leads" in data:
            leads = data["leads"]
            print(f"Leads type: {type(leads)}")
            print(f"Leads count: {len(leads) if isinstance(leads, list) else 'N/A'}")
        return

    if isinstance(data, list):
        print(f"Array length: {len(data)}")
        if len(data) > 0:
            print(f"First item type: {type(data[0])}")
            print(f"First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")

            # Check for nested arrays
            for i, item in enumerate(data):
                if isinstance(item, list):
                    print(f"WARNING: Item {i} is a nested list!")
                elif isinstance(item, dict):
                    for key, value in item.items():
                        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                            print(f"WARNING: Item {i} has nested array in key '{key}'")
        return

    print(f"Unknown structure: {type(data)}")


if __name__ == "__main__":
    leads_file = Path("leads.json")
    if leads_file.exists():
        check_structure(leads_file)
    else:
        print("leads.json not found")

    tracking_file = Path("job_tracking.json")
    if tracking_file.exists():
        print("\n" + "=" * 50 + "\n")
        check_structure(tracking_file)
    else:
        print("\njob_tracking.json not found")
