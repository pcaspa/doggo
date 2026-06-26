import math
from config import GESTURE_DIR
from utils import load_json, save_json, clamp
from config import SERVO_CONFIG
from gesture_manager import gesture_path

DOG_MAP = {
    "LF": [1, 2, 3],
    "RF": [4, 5, 6],
    "LH": [7, 8, 9],
    "RH": [10, 11, 12],
}

def _home_positions():
    cfg = load_json(SERVO_CONFIG)
    return {sid: data["home"] for sid, data in cfg.items()}

def _safe_positions(positions):
    cfg = load_json(SERVO_CONFIG)
    out = {}
    for sid, pos in positions.items():
        sid = str(sid)
        if sid in cfg:
            out[sid] = clamp(pos, cfg[sid]["min"], cfg[sid]["max"])
    return out

def _leg_offsets(leg, phase, stride=120, lift=140):
    # simple offset gait, no IK.
    # servo[0] shoulder small side balance
    # servo[1] hip forward/back
    # servo[2] knee lift/drop
    swing = math.sin(2 * math.pi * phase)
    lift_phase = max(0.0, math.sin(2 * math.pi * phase))

    shoulder = 0
    hip = int(stride * swing)
    knee = int(lift * lift_phase)

    # tune these signs as needed per robot
    if leg in ("RF", "RH"):
        hip = -hip
        knee = -knee

    return [shoulder, hip, knee]

def generate_crawl(name, cycles=2, dt=0.1, stride=80, lift=90):
    homes = _home_positions()
    phase_offsets = {
        "LF": 0.00,
        "RH": 0.25,
        "RF": 0.50,
        "LH": 0.75,
    }

    frames = []
    total_steps = int(cycles / dt)

    for i in range(total_steps + 1):
        t = round(i * dt, 3)
        positions = dict(homes)

        for leg, servos in DOG_MAP.items():
            phase = (i * dt + phase_offsets[leg]) % 1.0
            offsets = _leg_offsets(leg, phase, stride=stride, lift=lift)
            for sid, off in zip(servos, offsets):
                positions[str(sid)] = int(homes[str(sid)] + off)

        frames.append({
            "time": t,
            "positions": _safe_positions(positions)
        })

    gesture = {
        "name": name,
        "type": "frame_sequence",
        "generated_by": "generate_crawl",
        "servo_ids": list(range(1, 13)),
        "frames": frames
    }

    save_json(gesture_path(name), gesture)

def generate_trot(name, cycles=2, dt=0.08, stride=100, lift=110):
    homes = _home_positions()
    phase_offsets = {
        "LF": 0.00,
        "RH": 0.00,
        "RF": 0.50,
        "LH": 0.50,
    }

    frames = []
    total_steps = int(cycles / dt)

    for i in range(total_steps + 1):
        t = round(i * dt, 3)
        positions = dict(homes)

        for leg, servos in DOG_MAP.items():
            phase = (i * dt + phase_offsets[leg]) % 1.0
            offsets = _leg_offsets(leg, phase, stride=stride, lift=lift)
            for sid, off in zip(servos, offsets):
                positions[str(sid)] = int(homes[str(sid)] + off)

        frames.append({
            "time": t,
            "positions": _safe_positions(positions)
        })

    gesture = {
        "name": name,
        "type": "frame_sequence",
        "generated_by": "generate_trot",
        "servo_ids": list(range(1, 13)),
        "frames": frames
    }

    save_json(gesture_path(name), gesture)
