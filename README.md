# Robot Dog Controller

Python controller for Feetech/ST-series serial bus servos using Raspberry Pi, pose files, gesture files, behaviours, and simple generated gaits.

## Setup

```bash
cd ~/poppy
source venv/bin/activate
pip install feetech-servo-sdk
```

Copy this project into your Pi folder, then run:

```bash
python3 robot.py --help
```

## Typical commands

```bash
python3 robot.py servo scan
python3 robot.py servo info 1
python3 robot.py servo torque-off 1
python3 robot.py servo torque-on 1
python3 robot.py servo centre 1

python3 robot.py pose save stand 1 2 3
python3 robot.py pose play stand
python3 robot.py pose list

python3 robot.py gesture new wave
python3 robot.py gesture add wave stand 300 500
python3 robot.py gesture add wave paw_up 250 400
python3 robot.py gesture play wave
python3 robot.py gesture list

python3 robot.py behaviour new greet
python3 robot.py behaviour add-gesture greet wave
python3 robot.py behaviour play greet

python3 robot.py gait crawl crawl_slow
python3 robot.py gesture play crawl_slow
```

## Safety

Edit `servos.json` before running multi-servo motions. The code clamps all requested positions to min/home/max values.
Start with the robot suspended or powered safely.
