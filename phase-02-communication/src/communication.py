"""
Phase 2 - Communication module.

Every networking function lives here. detector.py and direction.py
(from Phase 1) know nothing about Wi-Fi, HTTP, or the ESP32, and stay
untouched.

Responsibility of this module:
    - Talk to the ESP32 over HTTP.
    - Remember the last direction that was sent.
    - Only send a new request when the direction actually changes,
      so we never spam the ESP32 with repeated identical requests.
"""

import requests

from config import ESP32_PORT, REQUEST_TIMEOUT


class DirectionSender:
    """Sends the current obstacle direction to the ESP32 over HTTP."""

    ENDPOINTS = {
        "LEFT": "/left",
        "CENTER": "/center",
        "RIGHT": "/right",
        "NO OBSTACLE": "/none",
        "NONE": "/none",
    }

    def __init__(self, esp32_ip, port=ESP32_PORT, timeout=REQUEST_TIMEOUT, enabled=True):
        self.base_url = f"http://{esp32_ip}:{port}"
        self.timeout = timeout
        self.enabled = enabled
        self.previous_direction = None

    def send_direction(self, direction):

        if direction == self.previous_direction:
            return False

        if not self.enabled:
            return False

        endpoint = self.ENDPOINTS.get(direction, "/none")
        url = self.base_url + endpoint

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Only remember the direction after a successful request.
            self.previous_direction = direction

            return True

        except requests.exceptions.RequestException as exc:
            print(f"[communication] Could not reach ESP32 at {url}: {exc}")
            return False