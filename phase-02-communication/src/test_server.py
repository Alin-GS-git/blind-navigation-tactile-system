"""
Phase 2 - Test server.

A lightweight stand-in for the ESP32's web server, so the Python side
of the communication layer can be tested on its own before real
hardware is available. It exposes the same endpoint the real
ESP32 sketch (../esp32/esp32_server.ino) will expose, and prints the
received occupancy state to the console - just like the ESP32 prints to its
Serial Monitor.

Run:
    python test_server.py

Then, in another terminal, point test_client.py (or main.py) at
127.0.0.1 to exercise the full request/response path locally.
"""

from flask import Flask, jsonify, request
from config import TEST_SERVER_PORT

app = Flask(__name__)


@app.route("/state", methods=["POST"])
def state():
    received_state = request.get_json(silent=True) or {}
    state = {
        "left": bool(received_state.get("left", False)),
        "center": bool(received_state.get("center", False)),
        "right": bool(received_state.get("right", False)),
    }
    print(f"Received state: {state}")
    return jsonify(status="OK", state=state)


if __name__ == "__main__":
    print("Mock ESP32 server running. Endpoint: POST /state")
    print(f"Point communication.DirectionSender at esp32_ip='127.0.0.1', port={TEST_SERVER_PORT}")
    app.run(host="0.0.0.0", port=TEST_SERVER_PORT)
