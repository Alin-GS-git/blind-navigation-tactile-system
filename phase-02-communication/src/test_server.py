"""
Phase 2 - Test server.

A lightweight stand-in for the ESP32's web server, so the Python side
of the communication layer can be tested on its own before real
hardware is available. It exposes the exact same endpoints the real
ESP32 sketch (../esp32/esp32_server.ino) will expose, and prints the
received direction to the console - just like the ESP32 prints to its
Serial Monitor.

Run:
    python test_server.py

Then, in another terminal, point test_client.py (or main.py) at
127.0.0.1 to exercise the full request/response path locally.
"""

from flask import Flask
from config import TEST_SERVER_PORT

app = Flask(__name__)


def _handle(direction):
    print(direction)
    return f"OK: {direction}\n"


@app.route("/left")
def left():
    return _handle("LEFT")


@app.route("/center")
def center():
    return _handle("CENTER")


@app.route("/right")
def right():
    return _handle("RIGHT")


@app.route("/none")
def none():
    return _handle("NONE")


if __name__ == "__main__":
    print("Mock ESP32 server running. Endpoints: /left /center /right /none")
    print(f"Point communication.DirectionSender at esp32_ip='127.0.0.1', port={TEST_SERVER_PORT}")
    app.run(host="0.0.0.0", port=TEST_SERVER_PORT)