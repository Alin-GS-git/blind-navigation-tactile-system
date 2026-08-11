"""
Phase 2 - Communication module.

Every networking function lives here. detector.py and direction.py
(from Phase 1) know nothing about Wi-Fi, HTTP, or the ESP32, and stay
untouched.

Responsibility of this module:
    - Talk to the ESP32 over HTTP.
    - Remember the last spatial state that was sent.
    - Only send a new request when the spatial state actually changes,
      so we never spam the ESP32 with repeated identical requests.
"""

import requests

# ------------------------------------------------------------
# Phase 2 configuration
#
# These values are defined here instead of importing "config"
# because Phase 1 also has a file named config.py.
#
# When Phase 1 imports this module, Python could otherwise load
# Phase 1's config.py instead of Phase 2's config.py.
# ------------------------------------------------------------

ESP32_PORT = 80
REQUEST_TIMEOUT = 1

# ------------------------------------------------------------
# Spatial state definition
# ------------------------------------------------------------

SPATIAL_LEVELS = (
    "head",
    "waist",
    "knee",
    "ground",
)

SPATIAL_REGIONS = (
    "left",
    "center",
    "right",
)


class DirectionSender:
    """Sends the current obstacle spatial state to the ESP32 over HTTP."""

    def __init__(
        self,
        esp32_ip,
        port=ESP32_PORT,
        timeout=REQUEST_TIMEOUT,
        enabled=True,
    ):
        self.base_url = f"http://{esp32_ip}:{port}"
        self.timeout = timeout
        self.enabled = enabled
        self.previous_state = None

    def _empty_state(self):
        return {
            level: {
                region: False
                for region in SPATIAL_REGIONS
            }
            for level in SPATIAL_LEVELS
        }

    def _normalize_level_state(self, value):
        normalized = {
            region: False
            for region in SPATIAL_REGIONS
        }

        if not isinstance(value, dict):
            return normalized

        for region in SPATIAL_REGIONS:
            normalized[region] = bool(
                value.get(region, False)
            )

        return normalized

    def _normalize_state(self, state):
        """
        Convert Phase 1's spatial state into the exact 3x4
        format expected by the ESP32.
        """

        normalized = self._empty_state()

        if not isinstance(state, dict):
            return normalized

        # Phase 1 provides:
        #
        # {
        #     "cells": {
        #         "head": {...},
        #         "waist": {...},
        #         "knee": {...},
        #         "ground": {...}
        #     },
        #     ...
        # }
        #
        # Accept both the complete Phase 1 object and the
        # cells dictionary itself.

        source = (
            state.get("cells")
            if isinstance(state.get("cells"), dict)
            else state
        )

        for level in SPATIAL_LEVELS:
            normalized[level] = (
                self._normalize_level_state(
                    source.get(level, {})
                )
            )

        return normalized

    def _state_key(self, state):
        """
        Create a hashable representation of the 3x4 state.

        This allows us to avoid repeatedly sending the exact
        same state to the ESP32.
        """

        return tuple(
            bool(state[level][region])
            for level in SPATIAL_LEVELS
            for region in SPATIAL_REGIONS
        )

    def send_state(self, state):
        """
        Send a spatial state to the ESP32.

        Returns:
            True  -> state was successfully sent
            False -> state was unchanged, disabled, or failed
        """

        normalized_state = self._normalize_state(state)

        state_key = self._state_key(
            normalized_state
        )

        # Do not repeatedly send identical states.
        if state_key == self.previous_state:
            return False

        if not self.enabled:
            return False

        url = self.base_url + "/state"

        try:
            response = requests.post(
                url,
                json=normalized_state,
                timeout=self.timeout,
            )

            response.raise_for_status()

            # Only remember the state after a successful
            # communication with the ESP32.
            self.previous_state = state_key

            print(
                f"[communication] Spatial state sent "
                f"to ESP32 at {self.base_url}"
            )

            return True

        except requests.exceptions.RequestException as exc:
            print(
                f"[communication] Could not reach ESP32 "
                f"at {url}: {exc}"
            )
            return False