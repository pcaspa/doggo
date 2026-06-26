import json
import os

def ensure_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved: {path}")

def clamp(value, min_val, max_val):
    return max(min_val, min(int(value), max_val))
