"""
Phase 2 - main entry point.

Receives a Phase 1 spatial state and forwards it to communication.py.
This file does not do detection or classification.
"""

from config import ESP32_IP
from communication import DirectionSender


def _empty_spatial_state():
    return {
        "head": {"left": False, "center": False, "right": False},
        "waist": {"left": False, "center": False, "right": False},
        "knee": {"left": False, "center": False, "right": False},
        "ground": {"left": False, "center": False, "right": False},
    }


def main(spatial_state=None, esp32_ip=ESP32_IP, communication_enabled=True):
    sender = DirectionSender(esp32_ip=esp32_ip, enabled=communication_enabled)

    if spatial_state is None:
        spatial_state = _empty_spatial_state()
        print("[main] No spatial state supplied; sending a neutral 3x4 state.")

    sent = sender.send_state(spatial_state)
    if sent:
        print(f"[main] Spatial state sent to ESP32 at {esp32_ip}")
    else:
        print("[main] Spatial state was not sent.")

    return sent


if __name__ == "__main__":
    main()
