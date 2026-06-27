import os
from config import POSE_DIR, SERVO_CONFIG, DEFAULT_SPEED
from utils import ensure_dirs, load_json, save_json
from servo_controller import ServoController

ensure_dirs(POSE_DIR)

def pose_path(name):
    return os.path.join(POSE_DIR, f"{name}.json")

def pose_exists(name):
    return os.path.exists(pose_path(name))

def load_pose(name):
    return load_json(pose_path(name))

def list_poses():
    if not os.path.isdir(POSE_DIR):
        return []
    return sorted([f[:-5] for f in os.listdir(POSE_DIR) if f.endswith(".json")])

def save_pose(name, servo_ids):
    controller = ServoController()
    positions = {}

    try:
        for sid in servo_ids:
            pos = controller.read_position(int(sid))
            if pos is not None:
                positions[str(sid)] = pos
    finally:
        controller.close()

    pose = {
        "name": name,
        "servo_ids": [int(x) for x in servo_ids],
        "positions": positions
    }

    save_json(pose_path(name), pose)

def play_pose(name, speed=DEFAULT_SPEED):
    pose = load_pose(name)
    controller = ServoController()

    try:
        for sid in pose["positions"].keys():
            controller.torque(int(sid), True)
        controller.move_many(pose["positions"], speed=speed)
    finally:
        controller.close()

    print(f"Played pose: {name}")

def save_home_pose():
    servos = load_json(SERVO_CONFIG)
    servo_ids = [int(x) for x in servos.keys()]
    positions = {sid: cfg["home"] for sid, cfg in servos.items()}

    pose = {
        "name": "home",
        "servo_ids": servo_ids,
        "positions": positions,
    }

    save_json(pose_path("home"), pose)

def show_pose(name):
    pose = load_pose(name)
    print(f"Pose: {pose['name']}")
    for sid, pos in pose["positions"].items():
        print(f"  {sid}: {pos}")
