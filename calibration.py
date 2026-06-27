import json
import time
from servo_controller import ServoController
from config import SERVO_CONFIG, ADDR_PRESENT_POSITION, ADDR_GOAL_POSITION, ADDR_MOVING_SPEED

JOINT_NAMES = [
    "LF_Shoulder", "LF_Hip", "LF_Knee",
    "RF_Shoulder", "RF_Hip", "RF_Knee",
    "LH_Shoulder", "LH_Hip", "LH_Knee",
    "RH_Shoulder", "RH_Hip", "RH_Knee",
]

DIRECTION_TEST_OFFSET = 20


def _read_raw_position(controller, servo_id):
    value, result, error = controller.packet.read2ByteTxRx(
        controller.port, int(servo_id), ADDR_PRESENT_POSITION
    )
    from scservo_sdk import COMM_SUCCESS
    if result != COMM_SUCCESS:
        raise RuntimeError(f"Failed to read position from servo {servo_id}")
    return value


def _move_raw(controller, servo_id, position, speed=200):
    controller.packet.write2ByteTxRx(
        controller.port, int(servo_id), ADDR_MOVING_SPEED, int(speed)
    )
    controller.packet.write2ByteTxRx(
        controller.port, int(servo_id), ADDR_GOAL_POSITION, int(position)
    )


def run_calibration(servo_id=None):
    controller = ServoController.__new__(ServoController)
    from scservo_sdk import PortHandler, PacketHandler
    from config import PORT, BAUD

    SCS_END = 0
    controller.config = {}
    controller.port = PortHandler(PORT)
    controller.packet = PacketHandler(SCS_END)

    if not controller.port.openPort():
        raise RuntimeError(f"Failed to open port {PORT}")
    if not controller.port.setBaudRate(BAUD):
        raise RuntimeError(f"Failed to set baud rate {BAUD}")

    try:
        _do_calibration(controller, servo_id)
    finally:
        controller.port.closePort()


def _do_calibration(controller, single_servo_id=None):
    print("\n=== Servo Calibration Wizard ===\n")

    # Load existing config for single-servo recalibration
    existing = {}
    if single_servo_id is not None:
        try:
            from utils import load_json
            existing = load_json(SERVO_CONFIG)
        except FileNotFoundError:
            print(f"No existing {SERVO_CONFIG} found. Run full calibration first.")
            return

    # Step 1: Scan
    print("Scanning servos...\n")
    found = controller.scan()

    if not found:
        print("No servos found. Check wiring and power.")
        return

    if single_servo_id is not None:
        if single_servo_id not in [sid for sid, _ in found]:
            print(f"Servo {single_servo_id} not found on bus.")
            return
        servo_ids = [single_servo_id]
        print(f"Recalibrating servo {single_servo_id}\n")
        # Build available joints: exclude joints already assigned to OTHER servos
        taken = set()
        for sid, cfg in existing.items():
            if int(sid) != single_servo_id:
                name = cfg.get("name", "")
                if name in JOINT_NAMES:
                    taken.add(name)
        available_joints = [(i, n) for i, n in enumerate(JOINT_NAMES, 1) if n not in taken]
    else:
        print("Found:\n")
        for sid, model in found:
            print(f"  ID {sid}")

        print()
        resp = input("Continue? (Y/N): ").strip().upper()
        if resp != "Y":
            print("Calibration cancelled.")
            return

        servo_ids = [sid for sid, _ in found]
        available_joints = list(enumerate(JOINT_NAMES, 1))

    result = dict(existing)

    for servo_id in servo_ids:
        print(f"\n--- Servo {servo_id} ---\n")

        # Turn off torque so user can move it by hand
        controller.torque(servo_id, False)

        # Step 2: Assign joint
        print("Which joint is this?\n")
        for idx, name in available_joints:
            print(f"  {idx:>2}  {name}")

        print()
        while True:
            try:
                choice = int(input("Enter number: ").strip())
                matches = [(i, n) for i, n in available_joints if i == choice]
                if matches:
                    joint_idx, joint_name = matches[0]
                    available_joints = [(i, n) for i, n in available_joints if i != choice]
                    break
                print("Invalid choice, try again.")
            except ValueError:
                print("Enter a number.")

        print(f"\n  -> {joint_name}\n")

        # Step 3: Home position
        print("Move the joint to its CENTRE (home) position.")
        input("Press ENTER when ready...")
        home = _read_raw_position(controller, servo_id)
        print(f"\n  Home = {home}\n")

        # Step 4: First limit
        print("Move to one end of the safe range.")
        input("Press ENTER when ready...")
        limit_a = _read_raw_position(controller, servo_id)
        print(f"\n  Limit A = {limit_a}\n")

        # Step 5: Second limit
        print("Move to the OTHER end of the safe range.")
        input("Press ENTER when ready...")
        limit_b = _read_raw_position(controller, servo_id)
        print(f"\n  Limit B = {limit_b}\n")

        min_pos = min(limit_a, limit_b, home)
        max_pos = max(limit_a, limit_b, home)

        # Step 6: Determine direction
        print("Move the joint back to centre for direction test.")
        input("Press ENTER when ready...")

        current = _read_raw_position(controller, servo_id)
        controller.torque(servo_id, True)
        target = current + DIRECTION_TEST_OFFSET
        _move_raw(controller, servo_id, target)
        time.sleep(0.5)

        print(f"\n  Moving +{DIRECTION_TEST_OFFSET}...")
        resp = input("\nDid it move FORWARD? (Y/N): ").strip().upper()

        if resp == "Y":
            sign = 1
        else:
            sign = -1

        print(f"\n  sign = {sign}\n")

        # Return to home and release
        _move_raw(controller, servo_id, home)
        time.sleep(0.3)
        controller.torque(servo_id, False)

        result[str(servo_id)] = {
            "name": joint_name,
            "home": home,
            "min": min_pos,
            "max": max_pos,
            "sign": sign,
        }

    # Write servos.json
    with open(SERVO_CONFIG, "w") as f:
        json.dump(result, f, indent=4)

    print(f"\nCalibration complete! Saved to {SERVO_CONFIG}")
    print(json.dumps(result, indent=4))
