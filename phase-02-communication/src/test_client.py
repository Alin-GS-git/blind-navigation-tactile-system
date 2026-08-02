"""
Phase 2 - Test client.

Tests the communication layer in isolation, with no camera and no
YOLO involved (Testing requirement #1). Simulates a stream of
detected directions - including repeats - and confirms that
DirectionSender only fires an HTTP request when the direction
actually changes.

Run this after uploading the ESP32 sketch.
"""

import time

from communication import DirectionSender
from config import ESP32_IP, ESP32_PORT

# Simulates: LEFT LEFT LEFT LEFT LEFT CENTER CENTER RIGHT
# Expected sends: LEFT, CENTER, RIGHT (3 requests total)
SIMULATED_DIRECTIONS = [
    "LEFT", "LEFT", "LEFT", "LEFT", "LEFT",
    "CENTER", "CENTER",
    "RIGHT",
]


def main():
    sender = DirectionSender(
        esp32_ip=ESP32_IP,
        port=ESP32_PORT,
        enabled=True,
    )

    sent_count = 0

    for direction in SIMULATED_DIRECTIONS:
        was_sent = sender.send_direction(direction)
        status = "SENT" if was_sent else "skipped (unchanged)"
        print(f"Direction: {direction:8s} -> {status}")

        if was_sent:
            sent_count += 1

        time.sleep(0.2)

    print(f"\nTotal requests sent: {sent_count} (expected 3)")


if __name__ == "__main__":
    main()