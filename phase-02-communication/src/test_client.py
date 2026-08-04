"""
Phase 2 - Test client.

Tests the communication layer in isolation, with no camera and no
YOLO involved (Testing requirement #1). Simulates a stream of
detected occupancy states - including repeats - and confirms that
DirectionSender only fires an HTTP request when the state
actually changes.

Run this after uploading the ESP32 sketch.
"""

import time

from communication import DirectionSender
from config import ESP32_IP, ESP32_PORT

# Simulates: NONE, LEFT only, CENTER only, RIGHT only,
# LEFT + CENTER, CENTER + RIGHT, LEFT + RIGHT, LEFT + CENTER + RIGHT
SIMULATED_STATES = [
    ("NONE", {"left": False, "center": False, "right": False}),
    ("LEFT only", {"left": True, "center": False, "right": False}),
    ("CENTER only", {"left": False, "center": True, "right": False}),
    ("RIGHT only", {"left": False, "center": False, "right": True}),
    ("LEFT + CENTER", {"left": True, "center": True, "right": False}),
    ("CENTER + RIGHT", {"left": False, "center": True, "right": True}),
    ("LEFT + RIGHT", {"left": True, "center": False, "right": True}),
    ("LEFT + CENTER + RIGHT", {"left": True, "center": True, "right": True}),
]


def main():
    sender = DirectionSender(
        esp32_ip=ESP32_IP,
        port=ESP32_PORT,
        enabled=True,
    )

    sent_count = 0

    for label, state in SIMULATED_STATES:
        was_sent = sender.send_state(state)
        status = "SENT" if was_sent else "skipped (unchanged)"
        print(f"State: {label:24s} -> {status}")

        if was_sent:
            sent_count += 1

        repeat_sent = sender.send_state(state)
        repeat_status = "SENT" if repeat_sent else "skipped (unchanged)"
        print(f"State: {label:24s} repeat -> {repeat_status}")

        if repeat_sent:
            sent_count += 1

        time.sleep(0.2)

    print(f"\nTotal requests sent: {sent_count} (expected 8)")


if __name__ == "__main__":
    main()
