"""
Phase 2 - Test server.

A lightweight stand-in for the ESP32's web server, so the Python side
of the communication layer can be tested on its own before real
hardware is available. It accepts the same POST /state JSON body the
real ESP32 sketch will receive and prints the normalized 3x4 state.
"""

from flask import Flask, jsonify, request

from config import TEST_SERVER_PORT


SPATIAL_LEVELS = ("head", "waist", "knee", "ground")
SPATIAL_REGIONS = ("left", "center", "right")

app = Flask(__name__)


def _empty_state():
    return {
        level: {region: False for region in SPATIAL_REGIONS}
        for level in SPATIAL_LEVELS
    }


def _normalize_state(received_state):
    normalized = _empty_state()

    if not isinstance(received_state, dict):
        return normalized

    source = received_state.get("cells") if isinstance(received_state.get("cells"), dict) else received_state

    for level in SPATIAL_LEVELS:
        level_state = source.get(level, {})
        if not isinstance(level_state, dict):
            continue
        for region in SPATIAL_REGIONS:
            normalized[level][region] = bool(level_state.get(region, False))

    return normalized


def _print_state(state):
    for level in SPATIAL_LEVELS:
        level_state = state[level]
        print(f"{level.upper()}:")
        print(f"  LEFT={'YES' if level_state['left'] else 'NO'}")
        print(f"  CENTER={'YES' if level_state['center'] else 'NO'}")
        print(f"  RIGHT={'YES' if level_state['right'] else 'NO'}")


@app.route("/state", methods=["POST"])
def state():
    received_state = request.get_json(silent=True)
    if received_state is None:
        return jsonify(status="ERROR", message="Invalid JSON"), 400

    normalized_state = _normalize_state(received_state)
    _print_state(normalized_state)
    return jsonify(status="OK", state=normalized_state)


if __name__ == "__main__":
    print("Mock ESP32 server running. Endpoint: POST /state")
    print(f"Point communication.DirectionSender at esp32_ip='127.0.0.1', port={TEST_SERVER_PORT}")
    app.run(host="0.0.0.0", port=TEST_SERVER_PORT)
