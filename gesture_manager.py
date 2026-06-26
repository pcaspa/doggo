import os
import time
import copy
from config import GESTURE_DIR, DEFAULT_SPEED, DEFAULT_DELAY_MS
from utils import ensure_dirs, load_json, save_json, clamp
from pose_manager import load_pose, pose_exists
from servo_controller import ServoController

ensure_dirs(GESTURE_DIR)

def gesture_path(name):
    return os.path.join(GESTURE_DIR, f"{name}.json")

def load_gesture(name):
    return load_json(gesture_path(name))

def save_gesture(name, gesture):
    save_json(gesture_path(name), gesture)

def list_gestures():
    if not os.path.isdir(GESTURE_DIR):
        return []
    return sorted([f[:-5] for f in os.listdir(GESTURE_DIR) if f.endswith(".json")])

def new_gesture(name):
    gesture = {
        "name": name,
        "type": "pose_sequence",
        "steps": []
    }
    save_gesture(name, gesture)

def add_pose_step(gesture_name, pose_name, speed=DEFAULT_SPEED, delay_ms=DEFAULT_DELAY_MS):
    if not pose_exists(pose_name):
        raise FileNotFoundError(f"Pose not found: {pose_name}")

    gesture = load_gesture(gesture_name)
    if "steps" not in gesture:
        gesture["steps"] = []

    gesture["steps"].append({
        "pose": pose_name,
        "speed": int(speed),
        "delay_ms": int(delay_ms)
    })

    save_gesture(gesture_name, gesture)

def build_gesture_interactive(name):
    new_gesture(name)
    print("Enter steps as: pose_name speed delay_ms")
    print("Example: stand 300 500")
    print("Type done when finished.")

    while True:
        line = input("> ").strip()
        if line.lower() in ("done", "q", "quit", "exit"):
            break

        parts = line.split()
        if len(parts) != 3:
            print("Expected: pose_name speed delay_ms")
            continue

        pose, speed, delay = parts
        add_pose_step(name, pose, int(speed), int(delay))

def play_gesture(name):
    gesture = load_gesture(name)
    controller = ServoController()

    try:
        if gesture.get("type") == "pose_sequence":
            for step in gesture.get("steps", []):
                pose = load_pose(step["pose"])
                speed = int(step.get("speed", DEFAULT_SPEED))
                delay = int(step.get("delay_ms", DEFAULT_DELAY_MS))

                for sid in pose["positions"].keys():
                    controller.torque(int(sid), True)

                controller.move_many(pose["positions"], speed=speed)
                print(f"Pose {step['pose']} speed={speed} delay={delay}ms")
                time.sleep(delay / 1000.0)

        else:
            frames = gesture.get("frames", [])
            if not frames:
                print("Gesture has no frames.")
                return

            servo_ids = gesture.get("servo_ids", [])
            for sid in servo_ids:
                controller.torque(int(sid), True)

            first = frames[0]
            controller.move_many(first["positions"], speed=300)
            time.sleep(1)

            last_time = first["time"]

            for frame in frames[1:]:
                delay = frame["time"] - last_time
                if delay > 0:
                    time.sleep(delay)

                controller.move_many(frame["positions"], speed=DEFAULT_SPEED)
                last_time = frame["time"]

    finally:
        controller.close()

    print(f"Played gesture: {name}")

def show_gesture(name):
    gesture = load_gesture(name)
    print(f"Gesture: {gesture.get('name', name)}")
    print(f"Type: {gesture.get('type', 'frame_sequence')}")

    if gesture.get("type") == "pose_sequence":
        for i, step in enumerate(gesture.get("steps", []), start=1):
            print(f"  {i}. pose={step['pose']} speed={step.get('speed')} delay_ms={step.get('delay_ms')}")
    else:
        print(f"  frames: {len(gesture.get('frames', []))}")

def reverse_gesture(name):
    gesture = load_gesture(name)
    new_name = name + "_reversed"
    reversed_gesture = copy.deepcopy(gesture)
    reversed_gesture["name"] = new_name

    if gesture.get("type") == "pose_sequence":
        reversed_gesture["steps"] = list(reversed(gesture.get("steps", [])))
    else:
        frames = gesture.get("frames", [])
        if frames:
            duration = frames[-1]["time"]
            new_frames = []
            for frame in reversed(frames):
                f = copy.deepcopy(frame)
                f["time"] = round(duration - frame["time"], 3)
                new_frames.append(f)
            new_frames.sort(key=lambda x: x["time"])
            reversed_gesture["frames"] = new_frames

    save_gesture(new_name, reversed_gesture)

def speed_gesture(name, factor):
    if factor <= 0:
        raise ValueError("Speed factor must be > 0")

    gesture = load_gesture(name)
    suffix = str(factor).replace(".", "_")
    new_name = f"{name}_speed_{suffix}"
    sped = copy.deepcopy(gesture)
    sped["name"] = new_name

    if gesture.get("type") == "pose_sequence":
        for step in sped.get("steps", []):
            step["delay_ms"] = max(1, int(step.get("delay_ms", DEFAULT_DELAY_MS) / factor))
    else:
        for frame in sped.get("frames", []):
            frame["time"] = round(frame["time"] / factor, 3)

    save_gesture(new_name, sped)

def mirror_gesture(name):
    gesture = load_gesture(name)
    controller = ServoController()
    cfg = controller.config
    controller.close()

    new_name = name + "_mirrored"
    mirrored = copy.deepcopy(gesture)
    mirrored["name"] = new_name

    if gesture.get("type") == "pose_sequence":
        # Pose-sequence mirroring is best done by creating mirrored poses.
        # This function preserves the sequence and renames it only.
        print("Pose-sequence mirror created as sequence copy only.")
        print("Create mirrored poses separately for true left/right mirror.")
    else:
        for frame in mirrored.get("frames", []):
            for sid, pos in list(frame.get("positions", {}).items()):
                if sid not in cfg:
                    continue
                mn = cfg[sid]["min"]
                mx = cfg[sid]["max"]
                frame["positions"][sid] = clamp(mx - (int(pos) - mn), mn, mx)

    save_gesture(new_name, mirrored)
