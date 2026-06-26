import os
import time
import random
from config import BEHAVIOUR_DIR
from utils import ensure_dirs, load_json, save_json
from gesture_manager import play_gesture

ensure_dirs(BEHAVIOUR_DIR)

def behaviour_path(name):
    return os.path.join(BEHAVIOUR_DIR, f"{name}.json")

def load_behaviour(name):
    return load_json(behaviour_path(name))

def save_behaviour(name, behaviour):
    save_json(behaviour_path(name), behaviour)

def list_behaviours():
    if not os.path.isdir(BEHAVIOUR_DIR):
        return []
    return sorted([f[:-5] for f in os.listdir(BEHAVIOUR_DIR) if f.endswith(".json")])

def new_behaviour(name):
    behaviour = {
        "name": name,
        "loop": False,
        "steps": []
    }
    save_behaviour(name, behaviour)

def add_gesture_step(behaviour_name, gesture_name):
    b = load_behaviour(behaviour_name)
    b.setdefault("steps", []).append({"gesture": gesture_name})
    save_behaviour(behaviour_name, b)

def add_wait_step(behaviour_name, delay_ms):
    b = load_behaviour(behaviour_name)
    b.setdefault("steps", []).append({"wait_ms": int(delay_ms)})
    save_behaviour(behaviour_name, b)

def add_random_step(behaviour_name, gesture_names):
    b = load_behaviour(behaviour_name)
    b.setdefault("steps", []).append({"random_gesture": list(gesture_names)})
    save_behaviour(behaviour_name, b)

def show_behaviour(name):
    b = load_behaviour(name)
    print(f"Behaviour: {b.get('name', name)}")
    print(f"Loop: {b.get('loop', False)}")
    for i, step in enumerate(b.get("steps", []), start=1):
        print(f"  {i}. {step}")

def play_behaviour(name, max_loops=1):
    b = load_behaviour(name)
    loop = bool(b.get("loop", False))
    loops = 0

    while True:
        for step in b.get("steps", []):
            if "gesture" in step:
                play_gesture(step["gesture"])

            elif "wait_ms" in step:
                time.sleep(int(step["wait_ms"]) / 1000.0)

            elif "random_gesture" in step:
                choices = step["random_gesture"]
                if choices:
                    play_gesture(random.choice(choices))

            elif "choice" in step:
                choices = step["choice"]
                if choices:
                    selected = random.choice(choices)
                    play_gesture(selected["gesture"] if isinstance(selected, dict) else selected)

        loops += 1
        if not loop:
            break
        if max_loops and loops >= max_loops:
            break

    print(f"Played behaviour: {name}")
