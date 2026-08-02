"""
Phase 2 - Test client.

Tests the communication layer in isolation, with no camera and no
YOLO involved (Testing requirement #1). Simulates a stream of
detected directions - including repeats - and confirms that
DirectionSender only fires an HTTP request when the direction
actually changes.

Run the mock server first (in another terminal):
    python test_server.py

Then run this:
    python test_client.py

You should see exactly 3 requests logged by the server (LEFT, CENTER,
RIGHT) even though 8 directions are "detected" below.
"""

import time
from communication import DirectionSender

# Simulates: LEFT LEFT LEFT LEFT LEFT CENTER CENTER RIGHT
# Expected sends: LEFT, CENTER, RIGHT (3 requests total)
SIMULATED_DIRECTIONS = [
    "LEFT", "LEFT", "LEFT", "LEFT", "LEFT",
    "CENTER", "CENTER",
    "RIGHT",
]


def main():
    # Point this at the mock server (127.0.0.1:5000) or a real ESP32 (its IP, port 80)
    sender = DirectionSender(esp32_ip="127.0.0.1", port=5000, enabled=True)

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
