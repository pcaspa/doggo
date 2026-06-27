"""
Diagnostic script for pose save/play issues.
Run: python3 diagnose.py
"""
import json
import os
import sys

def section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}\n")

def main():
    # 1. Check servos.json
    section("1. servos.json")
    try:
        with open("servos.json") as f:
            servos = json.load(f)
        print(f"Loaded {len(servos)} servos")
        for sid, cfg in servos.items():
            home = cfg.get("home")
            mn = cfg.get("min")
            mx = cfg.get("max")
            name = cfg.get("name", "?")
            issues = []
            if mn is not None and mx is not None and mn >= mx:
                issues.append(f"min ({mn}) >= max ({mx})")
            if home is not None and mn is not None and home < mn:
                issues.append(f"home ({home}) < min ({mn})")
            if home is not None and mx is not None and home > mx:
                issues.append(f"home ({home}) > max ({mx})")
            status = "  PROBLEMS: " + ", ".join(issues) if issues else "  OK"
            print(f"  ID {sid:>2} {name:<15} min={mn} home={home} max={mx} sign={cfg.get('sign')}{status}")
    except Exception as e:
        print(f"ERROR loading servos.json: {e}")
        return

    # 2. Check existing pose files
    section("2. Saved poses")
    pose_dir = "poses"
    if not os.path.isdir(pose_dir):
        print("No poses directory found")
    else:
        for fname in sorted(os.listdir(pose_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(pose_dir, fname)
            try:
                with open(path) as f:
                    pose = json.load(f)
                positions = pose.get("positions", {})
                print(f"  {fname}:")
                for sid, pos in positions.items():
                    cfg = servos.get(sid, {})
                    mn = cfg.get("min", 0)
                    mx = cfg.get("max", 4095)
                    home = cfg.get("home")
                    name = cfg.get("name", "?")
                    issues = []
                    if pos < mn:
                        issues.append(f"BELOW min ({mn})")
                    if pos > mx:
                        issues.append(f"ABOVE max ({mx})")
                    if home is not None:
                        diff = abs(pos - home)
                        if diff > 500:
                            issues.append(f"FAR from home ({home}, diff={diff})")
                    if sid not in servos:
                        issues.append("NOT in servos.json")
                    status = " *** " + ", ".join(issues) if issues else ""
                    print(f"    ID {sid:>2} {name:<15} pos={pos} (home={home}){status}")
            except Exception as e:
                print(f"  {fname}: ERROR - {e}")

    # 3. Live servo read (if hardware available)
    section("3. Live servo positions vs config home")
    try:
        from servo_controller import ServoController
        c = ServoController()
        try:
            for sid in sorted(servos.keys(), key=int):
                cfg = servos[sid]
                pos = c.read_position(int(sid))
                home = cfg["home"]
                if pos is None:
                    print(f"  ID {sid:>2} {cfg['name']:<15} FAILED TO READ")
                else:
                    diff = pos - home
                    flag = " *** LARGE OFFSET" if abs(diff) > 200 else ""
                    print(f"  ID {sid:>2} {cfg['name']:<15} current={pos} home={home} diff={diff:+d}{flag}")
        finally:
            c.close()
    except Exception as e:
        print(f"Could not connect to servos: {e}")

    # 4. Test move_servo clamping
    section("4. Clamping check")
    print("What move_servo would actually send for each servo's home position:")
    from utils import clamp
    for sid, cfg in servos.items():
        home = cfg["home"]
        mn = cfg["min"]
        mx = cfg["max"]
        clamped = clamp(home, mn, mx)
        if clamped != home:
            print(f"  ID {sid:>2} {cfg['name']:<15} home={home} CLAMPED to {clamped} *** PROBLEM")
        else:
            print(f"  ID {sid:>2} {cfg['name']:<15} home={home} -> {clamped} OK")

    section("Done")

if __name__ == "__main__":
    main()
