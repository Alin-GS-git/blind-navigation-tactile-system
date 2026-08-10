
"""
Steps 7, 8 & 10 - Divide the frame into LEFT / CENTER / RIGHT regions,
work out which regions each detected obstacle occupies, and smooth the
occupancy state over several frames so it doesn't flicker rapidly.

This version extends the original horizontal occupancy logic with a
configurable vertical split and a lightweight detection tracker so the
spatial output can represent LEFT / CENTER / RIGHT combined with
HEAD / WAIST / KNEE / GROUND.
"""

import cv2
from collections import deque


HORIZONTAL_REGIONS = ("left", "center", "right")
VERTICAL_REGIONS = ("head", "waist", "knee", "ground")


class DirectionClassifier:
    def __init__(self, frame_width, vertical_ratios=None):
        self.frame_width = frame_width
        self.left_boundary = frame_width / 3
        self.right_boundary = 2 * frame_width / 3
        self.vertical_ratios = self._normalize_vertical_ratios(vertical_ratios)

    def _normalize_vertical_ratios(self, vertical_ratios):
        defaults = {
            "head_end": 0.25,
            "waist_end": 0.55,
            "knee_end": 0.80,
        }

        if vertical_ratios is None:
            return defaults

        normalized = defaults.copy()
        normalized.update(vertical_ratios)
        return normalized

    def _empty_horizontal_state(self):
        return {region: False for region in HORIZONTAL_REGIONS}

    def _empty_vertical_state(self):
        return {region: False for region in VERTICAL_REGIONS}

    def _empty_cell_state(self):
        return {
            vertical: self._empty_horizontal_state()
            for vertical in VERTICAL_REGIONS
        }

    @staticmethod
    def _interval_overlaps(region_start, region_end, box_start, box_end):
        return box_start < region_end and box_end > region_start

    def _regions_from_interval(self, box_start, box_end, boundaries):
        regions = []

        for region_start, region_end, region_name in boundaries:
            if self._interval_overlaps(region_start, region_end, box_start, box_end):
                regions.append(region_name)

        return regions

    def _vertical_boundaries(self, frame_height):
        head_end = frame_height * self.vertical_ratios["head_end"]
        waist_end = frame_height * self.vertical_ratios["waist_end"]
        knee_end = frame_height * self.vertical_ratios["knee_end"]

        return [
            (0.0, head_end, "head"),
            (head_end, waist_end, "waist"),
            (waist_end, knee_end, "knee"),
            (knee_end, float(frame_height), "ground"),
        ]

    def classify_detection(self, detection, frame_height):
        x1, y1, x2, y2 = detection["bbox"]

        horizontal_regions = self._regions_from_interval(
            x1,
            x2,
            [
                (0.0, self.left_boundary, "left"),
                (self.left_boundary, self.right_boundary, "center"),
                (self.right_boundary, float(self.frame_width), "right"),
            ],
        )

        vertical_regions = self._regions_from_interval(
            y1,
            y2,
            self._vertical_boundaries(frame_height),
        )

        cells = self._empty_cell_state()
        for vertical_region in vertical_regions:
            for horizontal_region in horizontal_regions:
                cells[vertical_region][horizontal_region] = True

        return {
            "horizontal": horizontal_regions,
            "vertical": vertical_regions,
            "cells": cells,
        }

    def get_occupied_regions(self, detections):
        """Step 8 - merge every detection into a single horizontal occupancy state."""
        occupied = self._empty_horizontal_state()

        for detection in detections:
            x1, _, x2, _ = detection["bbox"]

            if x1 < self.left_boundary:
                occupied["left"] = True
            if x2 > self.left_boundary and x1 < self.right_boundary:
                occupied["center"] = True
            if x2 > self.right_boundary:
                occupied["right"] = True

        return occupied

    def get_spatial_state(self, detections, frame_height):
        """Build the full 3 x 4 occupancy grid from every detection."""
        spatial_state = {
            "horizontal": self._empty_horizontal_state(),
            "vertical": self._empty_vertical_state(),
            "cells": self._empty_cell_state(),
        }

        for detection in detections:
            detection_state = self.classify_detection(detection, frame_height)

            for region in detection_state["horizontal"]:
                spatial_state["horizontal"][region] = True

            for region in detection_state["vertical"]:
                spatial_state["vertical"][region] = True

            for vertical_region, horizontal_regions in detection_state["cells"].items():
                for horizontal_region, is_occupied in horizontal_regions.items():
                    spatial_state["cells"][vertical_region][horizontal_region] = (
                        spatial_state["cells"][vertical_region][horizontal_region]
                        or is_occupied
                    )

        return spatial_state

    def draw_regions(self, frame, frame_height=None):
        """Draw the horizontal thirds and, when available, the vertical bands."""
        h = frame.shape[0]
        x1 = int(self.left_boundary)
        x2 = int(self.right_boundary)
        cv2.line(frame, (x1, 0), (x1, h), (100, 100, 100), 1)
        cv2.line(frame, (x2, 0), (x2, h), (100, 100, 100), 1)

        if frame_height is None:
            return

        for boundary in self._vertical_boundaries(frame_height)[:-1]:
            _, region_end, _ = boundary
            y = int(region_end)
            cv2.line(frame, (0, y), (frame.shape[1], y), (80, 80, 80), 1)


class DirectionStabilizer:
    """Step 10 - smooth occupancy output over a rolling window so a
    single noisy frame doesn't cause a rapid flicker.
    Returns the most common occupancy state seen in the last
    `window_size` frames.
    """

    def __init__(self, window_size=5):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

    def _empty_horizontal_state(self):
        return {region: False for region in HORIZONTAL_REGIONS}

    def _empty_vertical_state(self):
        return {region: False for region in VERTICAL_REGIONS}

    def _empty_cell_state(self):
        return {
            vertical: self._empty_horizontal_state()
            for vertical in VERTICAL_REGIONS
        }

    def _normalize_horizontal_state(self, raw_state):
        if raw_state is None:
            return self._empty_horizontal_state()

        if isinstance(raw_state, str):
            normalized = self._empty_horizontal_state()
            if raw_state == "LEFT":
                normalized["left"] = True
            elif raw_state == "CENTER":
                normalized["center"] = True
            elif raw_state == "RIGHT":
                normalized["right"] = True
            return normalized

        if "horizontal" in raw_state and isinstance(raw_state["horizontal"], dict):
            raw_state = raw_state["horizontal"]

        normalized = self._empty_horizontal_state()
        for region in HORIZONTAL_REGIONS:
            normalized[region] = bool(raw_state.get(region, False))
        return normalized

    def _normalize_spatial_state(self, raw_state):
        if raw_state is None:
            return {
                "horizontal": self._empty_horizontal_state(),
                "vertical": self._empty_vertical_state(),
                "cells": self._empty_cell_state(),
            }

        if "cells" not in raw_state:
            horizontal = self._normalize_horizontal_state(raw_state)
            return {
                "horizontal": horizontal,
                "vertical": self._empty_vertical_state(),
                "cells": self._empty_cell_state(),
            }

        normalized_cells = self._empty_cell_state()
        for vertical_region in VERTICAL_REGIONS:
            for horizontal_region in HORIZONTAL_REGIONS:
                normalized_cells[vertical_region][horizontal_region] = bool(
                    raw_state.get("cells", {})
                    .get(vertical_region, {})
                    .get(horizontal_region, False)
                )

        normalized_horizontal = self._empty_horizontal_state()
        for horizontal_region in HORIZONTAL_REGIONS:
            normalized_horizontal[horizontal_region] = any(
                normalized_cells[vertical_region][horizontal_region]
                for vertical_region in VERTICAL_REGIONS
            )

        normalized_vertical = self._empty_vertical_state()
        for vertical_region in VERTICAL_REGIONS:
            normalized_vertical[vertical_region] = any(
                normalized_cells[vertical_region].values()
            )

        return {
            "horizontal": normalized_horizontal,
            "vertical": normalized_vertical,
            "cells": normalized_cells,
        }

    def _normalize_state(self, raw_state):
        if isinstance(raw_state, dict) and "cells" in raw_state:
            return {
                "kind": "spatial",
                "state": self._normalize_spatial_state(raw_state),
            }

        return {
            "kind": "horizontal",
            "state": self._normalize_horizontal_state(raw_state),
        }

    def _majority_vote(self, values):
        if not values:
            return False
        return sum(1 for value in values if value) >= (len(values) / 2)

    def update(self, raw_state):
        normalized = self._normalize_state(raw_state)
        self.history.append(normalized)

        if normalized["kind"] == "spatial":
            stabilized_cells = self._empty_cell_state()
            for vertical_region in VERTICAL_REGIONS:
                for horizontal_region in HORIZONTAL_REGIONS:
                    votes = [
                        state["state"]["cells"][vertical_region][horizontal_region]
                        for state in self.history
                        if state["kind"] == "spatial"
                    ]
                    stabilized_cells[vertical_region][horizontal_region] = self._majority_vote(votes)

            stabilized_horizontal = self._empty_horizontal_state()
            for horizontal_region in HORIZONTAL_REGIONS:
                stabilized_horizontal[horizontal_region] = any(
                    stabilized_cells[vertical_region][horizontal_region]
                    for vertical_region in VERTICAL_REGIONS
                )

            stabilized_vertical = self._empty_vertical_state()
            for vertical_region in VERTICAL_REGIONS:
                stabilized_vertical[vertical_region] = any(
                    stabilized_cells[vertical_region].values()
                )

            return {
                "horizontal": stabilized_horizontal,
                "vertical": stabilized_vertical,
                "cells": stabilized_cells,
            }

        stabilized_horizontal = self._empty_horizontal_state()
        for horizontal_region in HORIZONTAL_REGIONS:
            votes = [
                state["state"][horizontal_region]
                for state in self.history
                if state["kind"] == "horizontal"
            ]
            stabilized_horizontal[horizontal_region] = self._majority_vote(votes)

        return stabilized_horizontal


class DetectionTracker:
    """Lightweight frame-to-frame detection tracker for temporal consistency."""

    def __init__(self, iou_threshold=0.25, max_missed_frames=2):
        self.iou_threshold = iou_threshold
        self.max_missed_frames = max_missed_frames
        self.next_track_id = 1
        self.tracks = []

    @staticmethod
    def _bbox_iou(box_a, box_b):
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
            return 0.0

        intersection = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
        union = area_a + area_b - intersection

        if union <= 0:
            return 0.0

        return intersection / union

    def _new_track(self, detection):
        track = detection.copy()
        track["track_id"] = self.next_track_id
        track["missed_frames"] = 0
        track["visible"] = True
        track["age"] = 1
        track["hits"] = 1
        self.next_track_id += 1
        return track

    def update(self, detections):
        updated_tracks = []
        unmatched_tracks = self.tracks.copy()

        for detection in detections:
            best_track = None
            best_score = 0.0

            for track in unmatched_tracks:
                if track["label"] != detection["label"]:
                    continue

                score = self._bbox_iou(track["bbox"], detection["bbox"])
                if score > best_score:
                    best_score = score
                    best_track = track

            if best_track is not None and best_score >= self.iou_threshold:
                best_track.update(detection)
                best_track["missed_frames"] = 0
                best_track["visible"] = True
                best_track["age"] += 1
                best_track["hits"] += 1
                updated_tracks.append(best_track)
                unmatched_tracks.remove(best_track)
            else:
                updated_tracks.append(self._new_track(detection))

        for track in unmatched_tracks:
            track["missed_frames"] += 1
            track["visible"] = False
            track["age"] += 1
            if track["missed_frames"] <= self.max_missed_frames:
                updated_tracks.append(track)

        self.tracks = updated_tracks
        return [track.copy() for track in self.tracks]
