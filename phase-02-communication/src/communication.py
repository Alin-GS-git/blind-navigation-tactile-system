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


class DirectionSender:
    """Sends the current obstacle direction to the ESP32 over HTTP.

    A request is only sent when the direction differs from the
    previous one sent - e.g. five LEFT frames in a row produce a
    single HTTP request, not five.
    """

    # Maps the direction strings used in Phase 1 to ESP32 endpoints.
    ENDPOINTS = {
        "LEFT": "/left",
        "CENTER": "/center",
        "RIGHT": "/right",
        "NO OBSTACLE": "/none",
        "NONE": "/none",
    }

    def __init__(self, esp32_ip, port=80, timeout=1.0, enabled=True):
        """
        esp32_ip : IP address of the ESP32 on the local Wi-Fi network,
                   e.g. "192.168.1.42" (printed by the ESP32 to Serial
                   on boot).
        port     : HTTP port the ESP32 web server listens on (80 by default).
        timeout  : seconds to wait for a response before giving up.
        enabled  : set False to run the pipeline with communication
                   disabled (e.g. no ESP32 available yet).
        """
        self.base_url = f"http://{esp32_ip}:{port}"
        self.timeout = timeout
        self.enabled = enabled
        self.previous_direction = None

    def send_direction(self, direction):
        """Send `direction` to the ESP32 only if it changed since the
        last call. Returns True if an HTTP request was actually sent,
        False otherwise (no change, or communication disabled/failed).
        """
        if direction == self.previous_direction:
            return False

        self.previous_direction = direction

        if not self.enabled:
            return False

        endpoint = self.ENDPOINTS.get(direction, "/none")
        url = self.base_url + endpoint

        try:
            requests.get(url, timeout=self.timeout)
            return True
        except requests.exceptions.RequestException as exc:
            print(f"[communication] Could not reach ESP32 at {url}: {exc}")
            return False
