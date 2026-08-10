"""
Phase 2 - Test client.

Tests the communication layer in isolation, with no camera and no
YOLO involved. It replays a sequence of 3x4 spatial states and
confirms that DirectionSender only fires an HTTP request when the
state actually changes.
"""

import time

from communication import DirectionSender
from config import ESP32_IP, ESP32_PORT


SPATIAL_LEVELS = ("head", "waist", "knee", "ground")
SPATIAL_REGIONS = ("left", "center", "right")


def build_state(overrides=None):
    state = {
        level: {region: False for region in SPATIAL_REGIONS}
        for level in SPATIAL_LEVELS
    }

    if overrides is None:
        return state

    for level, regions in overrides.items():
        for region, is_occupied in regions.items():
            state[level][region] = bool(is_occupied)

    return state


TEST_SEQUENCE = [
    ("TEST 1: all false", build_state()),
    ("TEST 2: LEFT + HEAD", build_state({"head": {"left": True}})),
    ("TEST 3: CENTER + WAIST", build_state({"waist": {"center": True}})),
    ("TEST 3 repeat", build_state({"waist": {"center": True}})),
    ("TEST 3 repeat again", build_state({"waist": {"center": True}})),
    ("TEST 4: RIGHT + KNEE", build_state({"knee": {"right": True}})),
    ("TEST 5: LEFT + GROUND", build_state({"ground": {"left": True}})),
    (
        "TEST 6: multiple spatial regions simultaneously",
        build_state(
            {
                "head": {"left": True},
                "waist": {"center": True},
                "knee": {"right": True},
                "ground": {"left": True, "center": True},
            }
        ),
    ),
    ("TEST 7: all 12 regions occupied", build_state({
        "head": {"left": True, "center": True, "right": True},
        "waist": {"left": True, "center": True, "right": True},
        "knee": {"left": True, "center": True, "right": True},
        "ground": {"left": True, "center": True, "right": True},
    })),
    ("TEST 8: CENTER + KNEE", build_state({"knee": {"center": True}})),
]


def _print_state(label, state):
    print(label)
    for level in SPATIAL_LEVELS:
        level_state = state[level]
        print(
            f"  {level.upper():<6}: "
            f"L={'ON' if level_state['left'] else 'OFF'} "
            f"C={'ON' if level_state['center'] else 'OFF'} "
            f"R={'ON' if level_state['right'] else 'OFF'}"
        )


def main():
    sender = DirectionSender(
        esp32_ip=ESP32_IP,
        port=ESP32_PORT,
        enabled=True,
    )

    sent_count = 0

    for label, state in TEST_SEQUENCE:
        _print_state(label, state)
        was_sent = sender.send_state(state)
        status = "SENT" if was_sent else "skipped (unchanged)"
        print(f"  -> {status}")

        if was_sent:
            sent_count += 1

        time.sleep(0.2)
        print()

    print(f"Total requests sent: {sent_count} (expected 8)")


if __name__ == "__main__":
    main()
