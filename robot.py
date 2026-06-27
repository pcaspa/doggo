import argparse
import sys

from servo_controller import ServoController
from pose_manager import save_pose, play_pose, list_poses, show_pose
from gesture_manager import (
    new_gesture, add_pose_step, build_gesture_interactive, play_gesture,
    list_gestures, show_gesture, reverse_gesture, speed_gesture, mirror_gesture
)
from behaviour_manager import (
    new_behaviour, add_gesture_step, add_wait_step, add_random_step,
    play_behaviour, list_behaviours, show_behaviour
)
from gait_generator import generate_crawl, generate_trot
from calibration import run_calibration

def cmd_servo(args):
    c = ServoController()
    try:
        if args.servo_cmd == "scan":
            found = c.scan(args.start, args.end)
            if not found:
                print("No servos found.")
            for sid, model in found:
                print(f"Found servo ID {sid}, model {model}")

        elif args.servo_cmd == "info":
            info = c.info(args.servo_id)
            for k, v in info.items():
                print(f"{k}: {v}")

        elif args.servo_cmd == "centre":
            c.centre_servo(args.servo_id)
            print(f"Centred servo {args.servo_id}")

        elif args.servo_cmd == "home":
            c.home_all()
            print("Moved all configured servos home.")

        elif args.servo_cmd == "torque-on":
            c.torque(args.servo_id, True)
            print(f"Torque ON for servo {args.servo_id}")

        elif args.servo_cmd == "torque-off":
            c.torque(args.servo_id, False)
            print(f"Torque OFF for servo {args.servo_id}")

    finally:
        c.close()

def cmd_pose(args):
    if args.pose_cmd == "save":
        save_pose(args.name, args.servo_ids)

    elif args.pose_cmd == "play":
        play_pose(args.name, speed=args.speed)

    elif args.pose_cmd == "list":
        for p in list_poses():
            print(p)

    elif args.pose_cmd == "show":
        show_pose(args.name)

def cmd_gesture(args):
    if args.gesture_cmd == "new":
        new_gesture(args.name)

    elif args.gesture_cmd == "add":
        add_pose_step(args.name, args.pose, args.speed, args.delay_ms)

    elif args.gesture_cmd == "build":
        build_gesture_interactive(args.name)

    elif args.gesture_cmd == "play":
        play_gesture(args.name)

    elif args.gesture_cmd == "list":
        for g in list_gestures():
            print(g)

    elif args.gesture_cmd == "show":
        show_gesture(args.name)

    elif args.gesture_cmd == "reverse":
        reverse_gesture(args.name)

    elif args.gesture_cmd == "speed":
        speed_gesture(args.name, args.factor)

    elif args.gesture_cmd == "mirror":
        mirror_gesture(args.name)

def cmd_behaviour(args):
    if args.behaviour_cmd == "new":
        new_behaviour(args.name)

    elif args.behaviour_cmd == "add-gesture":
        add_gesture_step(args.name, args.gesture)

    elif args.behaviour_cmd == "add-wait":
        add_wait_step(args.name, args.delay_ms)

    elif args.behaviour_cmd == "add-random":
        add_random_step(args.name, args.gestures)

    elif args.behaviour_cmd == "play":
        play_behaviour(args.name, max_loops=args.max_loops)

    elif args.behaviour_cmd == "list":
        for b in list_behaviours():
            print(b)

    elif args.behaviour_cmd == "show":
        show_behaviour(args.name)

def cmd_gait(args):
    if args.gait_cmd == "crawl":
        generate_crawl(args.name, cycles=args.cycles, dt=args.dt, stride=args.stride, lift=args.lift)

    elif args.gait_cmd == "trot":
        generate_trot(args.name, cycles=args.cycles, dt=args.dt, stride=args.stride, lift=args.lift)

def build_parser():
    parser = argparse.ArgumentParser(description="Robot dog servo/pose/gesture/behaviour controller")
    sub = parser.add_subparsers(dest="cmd", required=True)

    servo = sub.add_parser("servo")
    servo_sub = servo.add_subparsers(dest="servo_cmd", required=True)

    s = servo_sub.add_parser("scan")
    s.add_argument("--start", type=int, default=1)
    s.add_argument("--end", type=int, default=30)

    s = servo_sub.add_parser("info")
    s.add_argument("servo_id", type=int)

    s = servo_sub.add_parser("centre")
    s.add_argument("servo_id", type=int)

    servo_sub.add_parser("home")

    s = servo_sub.add_parser("torque-on")
    s.add_argument("servo_id", type=int)

    s = servo_sub.add_parser("torque-off")
    s.add_argument("servo_id", type=int)

    pose = sub.add_parser("pose")
    pose_sub = pose.add_subparsers(dest="pose_cmd", required=True)

    p = pose_sub.add_parser("save")
    p.add_argument("name")
    p.add_argument("servo_ids", nargs="+", type=int)

    p = pose_sub.add_parser("play")
    p.add_argument("name")
    p.add_argument("--speed", type=int, default=300)

    pose_sub.add_parser("list")

    p = pose_sub.add_parser("show")
    p.add_argument("name")

    gesture = sub.add_parser("gesture")
    gesture_sub = gesture.add_subparsers(dest="gesture_cmd", required=True)

    g = gesture_sub.add_parser("new")
    g.add_argument("name")

    g = gesture_sub.add_parser("add")
    g.add_argument("name")
    g.add_argument("pose")
    g.add_argument("speed", type=int)
    g.add_argument("delay_ms", type=int)

    g = gesture_sub.add_parser("build")
    g.add_argument("name")

    g = gesture_sub.add_parser("play")
    g.add_argument("name")

    gesture_sub.add_parser("list")

    g = gesture_sub.add_parser("show")
    g.add_argument("name")

    g = gesture_sub.add_parser("reverse")
    g.add_argument("name")

    g = gesture_sub.add_parser("speed")
    g.add_argument("name")
    g.add_argument("factor", type=float)

    g = gesture_sub.add_parser("mirror")
    g.add_argument("name")

    behaviour = sub.add_parser("behaviour")
    behaviour_sub = behaviour.add_subparsers(dest="behaviour_cmd", required=True)

    b = behaviour_sub.add_parser("new")
    b.add_argument("name")

    b = behaviour_sub.add_parser("add-gesture")
    b.add_argument("name")
    b.add_argument("gesture")

    b = behaviour_sub.add_parser("add-wait")
    b.add_argument("name")
    b.add_argument("delay_ms", type=int)

    b = behaviour_sub.add_parser("add-random")
    b.add_argument("name")
    b.add_argument("gestures", nargs="+")

    b = behaviour_sub.add_parser("play")
    b.add_argument("name")
    b.add_argument("--max-loops", type=int, default=1)

    behaviour_sub.add_parser("list")

    b = behaviour_sub.add_parser("show")
    b.add_argument("name")

    sub.add_parser("calibrate")

    gait = sub.add_parser("gait")
    gait_sub = gait.add_subparsers(dest="gait_cmd", required=True)

    c = gait_sub.add_parser("crawl")
    c.add_argument("name")
    c.add_argument("--cycles", type=int, default=2)
    c.add_argument("--dt", type=float, default=0.1)
    c.add_argument("--stride", type=int, default=80)
    c.add_argument("--lift", type=int, default=90)

    t = gait_sub.add_parser("trot")
    t.add_argument("name")
    t.add_argument("--cycles", type=int, default=2)
    t.add_argument("--dt", type=float, default=0.08)
    t.add_argument("--stride", type=int, default=100)
    t.add_argument("--lift", type=int, default=110)

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "calibrate":
        run_calibration()
    elif args.cmd == "servo":
        cmd_servo(args)
    elif args.cmd == "pose":
        cmd_pose(args)
    elif args.cmd == "gesture":
        cmd_gesture(args)
    elif args.cmd == "behaviour":
        cmd_behaviour(args)
    elif args.cmd == "gait":
        cmd_gait(args)
    else:
        parser.print_help()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
