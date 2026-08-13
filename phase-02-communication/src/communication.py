"""
Phase 2 - Communication Module

This module is responsible only for communication between
the laptop and the ESP32.

Phase 1 is responsible for:
    - Camera input
    - YOLO object detection
    - Object tracking
    - 3x4 spatial classification

Phase 2 is responsible for:
    - Receiving the 3x4 spatial state from Phase 1
    - Converting it into the required JSON format
    - Sending it to the ESP32 over Wi-Fi using HTTP
    - Avoiding duplicate HTTP requests

Phase 3 is responsible for:
    - Receiving the state on the ESP32
    - Controlling the tactile servos

The communication format is:

{
    "head": {
        "left": false,
        "center": false,
        "right": false
    },
    "waist": {
        "left": false,
        "center": false,
        "right": false
    },
    "knee": {
        "left": false,
        "center": false,
        "right": false
    },
    "ground": {
        "left": false,
        "center": false,
        "right": false
    }
}
"""

import requests


# ============================================================
# SPATIAL STATE DEFINITION
# ============================================================

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


# ============================================================
# DIRECTION SENDER
# ============================================================

class DirectionSender:
    """
    Sends the 3x4 spatial state from Phase 1 to the ESP32.

    The sender does not perform object detection or spatial
    classification. It only handles network communication.
    """

    def __init__(
        self,
        esp32_ip,
        port=80,
        timeout=1,
        enabled=True,
    ):
        self.esp32_ip = esp32_ip
        self.port = port
        self.timeout = timeout
        self.enabled = enabled

        self.base_url = (
            f"http://{esp32_ip}:{port}"
        )

        # Stores the last successfully transmitted state.
        #
        # This prevents sending the same state repeatedly.
        self.previous_state = None


    # ========================================================
    # STATE CREATION
    # ========================================================

    @staticmethod
    def _empty_state():
        """
        Create an empty 3x4 spatial state.

        Every cell is initially False.
        """

        return {
            level: {
                region: False
                for region in SPATIAL_REGIONS
            }
            for level in SPATIAL_LEVELS
        }


    @staticmethod
    def _normalize_level_state(value):
        """
        Normalize one vertical level.

        Example input:

            {
                "left": True,
                "center": False,
                "right": True
            }

        Missing or invalid values are treated as False.
        """

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
        Convert Phase 1's spatial state into the exact
        3x4 format expected by the ESP32.

        Phase 1 produces a complete object containing:

            {
                "cells": {
                    "head": {...},
                    "waist": {...},
                    "knee": {...},
                    "ground": {...}
                },
                "horizontal": {...},
                ...
            }

        Only "cells" is required for Phase 2 communication.

        The method also accepts the cells dictionary directly.
        """

        normalized = self._empty_state()

        if not isinstance(state, dict):
            return normalized

        # If the complete Phase 1 spatial state was supplied,
        # use its "cells" section.
        #
        # Otherwise assume that the supplied object is already
        # the cells dictionary.

        cells = state.get("cells")

        if isinstance(cells, dict):
            source = cells
        else:
            source = state

        # Normalize every vertical level.
        for level in SPATIAL_LEVELS:

            normalized[level] = (
                self._normalize_level_state(
                    source.get(level, {})
                )
            )

        return normalized


    # ========================================================
    # STATE COMPARISON
    # ========================================================

    @staticmethod
    def _state_key(state):
        """
        Convert the 3x4 state into a hashable tuple.

        The order is:

            HEAD:
                LEFT, CENTER, RIGHT

            WAIST:
                LEFT, CENTER, RIGHT

            KNEE:
                LEFT, CENTER, RIGHT

            GROUND:
                LEFT, CENTER, RIGHT
        """

        return tuple(
            bool(state[level][region])
            for level in SPATIAL_LEVELS
            for region in SPATIAL_REGIONS
        )


    # ========================================================
    # SEND STATE
    # ========================================================

    def send_state(self, state):
        """
        Send the current spatial state to the ESP32.

        Returns:

            True:
                A new state was successfully transmitted.

            False:
                The state was unchanged, communication was
                disabled, or the transmission failed.
        """

        # ----------------------------------------------------
        # Convert Phase 1 state to clean 3x4 state
        # ----------------------------------------------------

        normalized_state = self._normalize_state(
            state
        )

        # ----------------------------------------------------
        # Create comparison key
        # ----------------------------------------------------

        state_key = self._state_key(
            normalized_state
        )

        # ----------------------------------------------------
        # Do not send duplicate states
        # ----------------------------------------------------

        if state_key == self.previous_state:

            return False

        # ----------------------------------------------------
        # Communication disabled
        # ----------------------------------------------------

        if not self.enabled:

            return False

        # ----------------------------------------------------
        # ESP32 endpoint
        # ----------------------------------------------------

        url = (
            self.base_url
            + "/state"
        )

        # ----------------------------------------------------
        # Send HTTP POST request
        # ----------------------------------------------------

        try:

            response = requests.post(
                url,
                json=normalized_state,
                timeout=self.timeout,
            )

            # Raise an exception for HTTP errors such as
            # 400, 404, 500, etc.
            response.raise_for_status()

            # Only remember the state after the ESP32
            # successfully accepted it.
            self.previous_state = state_key

            print(
                "[communication] "
                f"Spatial state sent to ESP32 at "
                f"{self.base_url}"
            )

            return True

        except requests.exceptions.RequestException as exc:

            print(
                "[communication] "
                f"Could not reach ESP32 at {url}: {exc}"
            )

            # Do NOT update previous_state here.
            #
            # This is important because the same state will
            # be attempted again on a later frame if the
            # network connection becomes available.

            return False