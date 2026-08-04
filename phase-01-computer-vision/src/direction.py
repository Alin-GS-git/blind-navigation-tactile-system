"""
Steps 7, 8 & 10 - Divide the frame into LEFT / CENTER / RIGHT regions,
work out which regions each detected obstacle occupies, and smooth the
occupancy state over several frames so it doesn't flicker rapidly.
"""

import cv2
from collections import deque


class DirectionClassifier:
    def __init__(self, frame_width):
        self.frame_width = frame_width
        self.left_boundary = frame_width / 3
        self.right_boundary = 2 * frame_width / 3

    def _empty_state(self):
        return {"left": False, "center": False, "right": False}

    def _region_state_from_bbox(self, bbox):
        x1, _, x2, _ = bbox

        left_occupied = x1 < self.left_boundary
        center_occupied = x2 > self.left_boundary and x1 < self.right_boundary
        right_occupied = x2 > self.right_boundary

        return {
            "left": left_occupied,
            "center": center_occupied,
            "right": right_occupied,
        }

    def get_occupied_regions(self, detections):
        """Step 8 - merge every detection into a single occupancy state."""
        occupied = self._empty_state()

        for detection in detections:
            detection_state = self._region_state_from_bbox(detection["bbox"])
            for region, is_occupied in detection_state.items():
                occupied[region] = occupied[region] or is_occupied

        return occupied

    def draw_regions(self, frame):
        """Step 7 - draw the two dividing lines so regions are visible."""
        h = frame.shape[0]
        x1 = int(self.left_boundary)
        x2 = int(self.right_boundary)
        cv2.line(frame, (x1, 0), (x1, h), (100, 100, 100), 1)
        cv2.line(frame, (x2, 0), (x2, h), (100, 100, 100), 1)


class DirectionStabilizer:
    """Step 10 - smooth occupancy output over a rolling window so a
    single noisy frame doesn't cause a rapid flicker.
    Returns the most common occupancy state seen in the last
    `window_size` frames.
    """

    def __init__(self, window_size=5):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

    def _empty_state(self):
        return {"left": False, "center": False, "right": False}

    def _normalize_state(self, raw_state):
        if raw_state is None:
            return self._empty_state()

        if isinstance(raw_state, str):
            normalized = self._empty_state()
            if raw_state == "LEFT":
                normalized["left"] = True
            elif raw_state == "CENTER":
                normalized["center"] = True
            elif raw_state == "RIGHT":
                normalized["right"] = True
            return normalized

        normalized = self._empty_state()
        for region in normalized:
            normalized[region] = bool(raw_state.get(region, False))
        return normalized

    def update(self, raw_state):
        state = self._normalize_state(raw_state)
        self.history.append(state)

        stabilized = self._empty_state()
        history_length = len(self.history)

        for region in stabilized:
            votes = sum(1 for item in self.history if item[region])
            stabilized[region] = votes > (history_length / 2)

        return stabilized
