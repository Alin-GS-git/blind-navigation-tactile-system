"""
Phase 2 - Communication module.

Every networking function lives here. detector.py and direction.py
(from Phase 1) know nothing about Wi-Fi, HTTP, or the ESP32, and stay
untouched.

Responsibility of this module:
    - Talk to the ESP32 over HTTP.
    - Remember the last occupancy state that was sent.
    - Only send a new request when the occupancy state actually changes,
      so we never spam the ESP32 with repeated identical requests.
"""

import requests

from config import ESP32_PORT, REQUEST_TIMEOUT


class DirectionSender:
    """Sends the current obstacle occupancy state to the ESP32 over HTTP."""

    def __init__(self, esp32_ip, port=ESP32_PORT, timeout=REQUEST_TIMEOUT, enabled=True):
        self.base_url = f"http://{esp32_ip}:{port}"
        self.timeout = timeout
        self.enabled = enabled
        self.previous_state = None

    def _empty_state(self):
        return {
            "left": False,
            "center": False,
            "right": False
        }

    def _state_key(self, state):
        return (
            bool(state["left"]),
            bool(state["center"]),
            bool(state["right"])
        )

    def _normalize_state(self, state):
        if isinstance(state, str):
            normalized = self._empty_state()

            if state == "LEFT":
                normalized["left"] = True
            elif state == "CENTER":
                normalized["center"] = True
            elif state == "RIGHT":
                normalized["right"] = True

            return normalized

        normalized = self._empty_state()

        for region in normalized:
            normalized[region] = bool(state.get(region, False))

        return normalized

    def send_state(self, state):
        normalized_state = self._normalize_state(state)
        state_key = self._state_key(normalized_state)

        if state_key == self.previous_state:
            return False

        if not self.enabled:
            return False

        url = self.base_url + "/state"

        params = {
            "left": int(normalized_state["left"]),
            "center": int(normalized_state["center"]),
            "right": int(normalized_state["right"])
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout
            )

            response.raise_for_status()

            self.previous_state = state_key
            return True

        except requests.exceptions.RequestException as exc:
            print(f"[communication] Could not reach ESP32 at {response.url if 'response' in locals() else url}: {exc}")
            return False

    def send_direction(self, direction):
        return self.send_state(self._normalize_state(direction))