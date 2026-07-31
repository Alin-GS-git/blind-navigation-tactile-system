"""
Steps 7, 8 & 10 - Divide the frame into LEFT / CENTER / RIGHT regions,
work out which region an obstacle's center falls in, and smooth the
output over several frames so it doesn't flicker rapidly.
"""

import cv2
from collections import deque, Counter


class DirectionClassifier:
    def __init__(self, frame_width):
        self.frame_width = frame_width
        self.left_boundary = frame_width / 3
        self.right_boundary = 2 * frame_width / 3

    def get_direction(self, center_x):
        """Step 8 - map an obstacle's x-center to LEFT / CENTER / RIGHT."""
        if center_x < self.left_boundary:
            return "LEFT"
        elif center_x < self.right_boundary:
            return "CENTER"
        else:
            return "RIGHT"

    def draw_regions(self, frame):
        """Step 7 - draw the two dividing lines so regions are visible."""
        h = frame.shape[0]
        x1 = int(self.left_boundary)
        x2 = int(self.right_boundary)
        cv2.line(frame, (x1, 0), (x1, h), (100, 100, 100), 1)
        cv2.line(frame, (x2, 0), (x2, h), (100, 100, 100), 1)


class DirectionStabilizer:
    """Step 10 - smooth direction output over a rolling window so a
    single noisy frame doesn't cause a rapid left/right/center flicker.
    Returns the most common direction seen in the last `window_size`
    frames.
    """

    def __init__(self, window_size=5):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

    def update(self, raw_direction):
        self.history.append(raw_direction)
        most_common, _ = Counter(self.history).most_common(1)[0]
        return most_common
