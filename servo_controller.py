from scservo_sdk import *
from config import *
from utils import load_json, clamp

class ServoController:
    def __init__(self):
        self.config = load_json(SERVO_CONFIG)
        self.port = PortHandler(PORT)
        self.packet = PacketHandler(SCS_END)

        if not self.port.openPort():
            raise RuntimeError(f"Failed to open port {PORT}")

        if not self.port.setBaudRate(BAUD):
            raise RuntimeError(f"Failed to set baud rate {BAUD}")

    def close(self):
        self.port.closePort()

    def get_limits(self, servo_id):
        sid = str(servo_id)
        if sid not in self.config:
            raise KeyError(f"Servo {servo_id} missing from {SERVO_CONFIG}")
        return self.config[sid]

    def all_servo_ids(self):
        return [int(x) for x in self.config.keys()]

    def torque(self, servo_id, enabled):
        value = 1 if enabled else 0
        result, error = self.packet.write1ByteTxRx(
            self.port, int(servo_id), ADDR_TORQUE_ENABLE, value
        )
        return result, error

    def read1(self, servo_id, addr):
        value, result, error = self.packet.read1ByteTxRx(self.port, int(servo_id), addr)
        if result != COMM_SUCCESS:
            return None
        return value

    def read2(self, servo_id, addr):
        value, result, error = self.packet.read2ByteTxRx(self.port, int(servo_id), addr)
        if result != COMM_SUCCESS:
            return None
        return value

    def read_position(self, servo_id):
        return self.read2(servo_id, ADDR_PRESENT_POSITION)

    def move_servo(self, servo_id, position, speed=DEFAULT_SPEED):
        limits = self.get_limits(servo_id)
        safe_position = clamp(position, limits["min"], limits["max"])

        self.packet.write2ByteTxRx(self.port, int(servo_id), ADDR_MOVING_SPEED, int(speed))
        self.packet.write2ByteTxRx(self.port, int(servo_id), ADDR_GOAL_POSITION, int(safe_position))

        return safe_position

    def move_many(self, positions, speed=DEFAULT_SPEED):
        applied = {}
        for sid, pos in positions.items():
            applied[str(sid)] = self.move_servo(int(sid), int(pos), speed)
        return applied

    def centre_servo(self, servo_id):
        limits = self.get_limits(servo_id)
        self.torque(servo_id, True)
        return self.move_servo(servo_id, limits["home"])

    def torque_off_all(self):
        for sid in self.config.keys():
            self.torque(int(sid), False)

    def home_all(self):
        for sid, cfg in self.config.items():
            self.torque(int(sid), True)
            self.move_servo(int(sid), cfg["home"])

    def scan(self, start_id=1, end_id=30):
        found = []
        for servo_id in range(start_id, end_id + 1):
            model, result, error = self.packet.ping(self.port, servo_id)
            if result == COMM_SUCCESS:
                found.append((servo_id, model))
        return found

    def info(self, servo_id):
        limits = self.get_limits(servo_id)
        return {
            "id": int(servo_id),
            "name": limits.get("name", ""),
            "min": limits["min"],
            "home": limits["home"],
            "max": limits["max"],
            "sign": limits.get("sign", 1),
            "position": self.read_position(servo_id),
            "speed": self.read2(servo_id, ADDR_PRESENT_SPEED),
            "load": self.read2(servo_id, ADDR_PRESENT_LOAD),
            "voltage": self.read1(servo_id, ADDR_PRESENT_VOLTAGE),
            "temperature": self.read1(servo_id, ADDR_PRESENT_TEMPERATURE),
            "moving": self.read1(servo_id, ADDR_MOVING),
        }
