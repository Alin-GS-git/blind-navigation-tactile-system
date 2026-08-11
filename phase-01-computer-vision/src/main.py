"""
Phase 1 - Computer Vision Obstacle Detection

Entry point: opens the configured camera source, runs detection
each frame, collects the occupied LEFT / CENTER / RIGHT regions,
and draws everything on screen.

The stabilized 3x4 spatial state is also sent to the ESP32 through
the Phase 2 communication module.

Run with:
python main.py

Quit with:
press 'q' in the video window
"""

import time
import sys
from pathlib import Path

import cv2

from detector import ObstacleDetector
from direction import (
    DirectionClassifier,
    DirectionStabilizer,
    DetectionTracker,
)
from config import (
    CAMERA_SOURCE,
    CONF_THRESHOLD,
    STABILIZATION_WINDOW,
    TRACKER_IOU_THRESHOLD,
    TRACKER_MAX_MISSED_FRAMES,
    VERTICAL_REGION_RATIOS,
)

# ------------------------------------------------------------
# Import Phase 2 communication module
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE_2_SRC = PROJECT_ROOT / "phase-02-communication" / "src"

if str(PHASE_2_SRC) not in sys.path:
    sys.path.insert(0, str(PHASE_2_SRC))

from communication import DirectionSender


HORIZONTAL_ABBREVIATIONS = {
    "left": "L",
    "center": "C",
    "right": "R",
}

VERTICAL_ABBREVIATIONS = {
    "head": "HEAD",
    "waist": "WAIST",
    "knee": "KNEE",
    "ground": "GROUND",
}


def _format_region_flags(
    region_state,
    region_order,
    abbreviations,
):
    values = []

    for region in region_order:
        yes_no = "YES" if region_state[region] else "NO"
        values.append(
            f"{abbreviations[region]}:{yes_no}"
        )

    return "  ".join(values)


def _format_detection_regions(classification):
    horizontal = (
        "/".join(
            HORIZONTAL_ABBREVIATIONS[region]
            for region in classification["horizontal"]
        )
        if classification["horizontal"]
        else "NONE"
    )

    vertical = (
        "/".join(
            VERTICAL_ABBREVIATIONS[region]
            for region in classification["vertical"]
        )
        if classification["vertical"]
        else "NONE"
    )

    return f"H:{horizontal}  V:{vertical}"


def main(
    camera_source=CAMERA_SOURCE,
    conf_threshold=CONF_THRESHOLD,
):
    # --------------------------------------------------------
    # Open configured camera source
    # --------------------------------------------------------
    cap = cv2.VideoCapture(camera_source)

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open camera source: {camera_source}\n"
            "Check that the camera is available and the IP Webcam "
            "server is running."
        )

    # Reduce buffering for network camera streams.
    if isinstance(camera_source, str):
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # --------------------------------------------------------
    # Phase 1 - Detection components
    # --------------------------------------------------------
    detector = ObstacleDetector(
        conf_threshold=conf_threshold
    )

    stabilizer = DirectionStabilizer(
        window_size=STABILIZATION_WINDOW
    )

    tracker = DetectionTracker(
        iou_threshold=TRACKER_IOU_THRESHOLD,
        max_missed_frames=TRACKER_MAX_MISSED_FRAMES,
    )

    # --------------------------------------------------------
    # Phase 2 - ESP32 communication
    #
    # DirectionSender already handles the 3x4 spatial state
    # and sends it to the ESP32 through /state.
    # --------------------------------------------------------
    sender = DirectionSender(
        esp32_ip="192.168.1.84",
        enabled=True,
    )

    prev_time = time.time()

    print("Starting Phase 1 obstacle detection.")
    print(f"Camera source: {camera_source}")
    print("Phase 2 ESP32 communication: ENABLED")
    print("ESP32 IP: 192.168.1.84")
    print("Press 'q' to quit.")

    try:
        while True:

            # ------------------------------------------------
            # Read frame
            # ------------------------------------------------
            ok, frame = cap.read()

            if not ok:
                print(
                    "Failed to read frame from camera. "
                    "Stopping."
                )
                break

            frame_height, frame_width = frame.shape[:2]

            classifier = DirectionClassifier(
                frame_width,
                vertical_ratios=VERTICAL_REGION_RATIOS,
            )

            # ------------------------------------------------
            # Detect all obstacles
            # ------------------------------------------------
            detections = detector.detect(frame)

            # ------------------------------------------------
            # Track detections across frames to improve
            # temporal consistency without changing the
            # detector output.
            # ------------------------------------------------
            tracked_detections = tracker.update(
                detections
            )

            # ------------------------------------------------
            # Inspect EVERY obstacle and determine which
            # regions are occupied.
            # ------------------------------------------------
            raw_spatial_state = (
                classifier.get_spatial_state(
                    tracked_detections,
                    frame_height,
                )
            )

            # ------------------------------------------------
            # Stabilize region states
            # ------------------------------------------------
            spatial_state = stabilizer.update(
                raw_spatial_state
            )

            # ------------------------------------------------
            # PHASE 2 CONNECTION
            #
            # Send the live stabilized 3x4 spatial state
            # to the ESP32.
            #
            # Phase 2 handles the HTTP request and only sends
            # when the state changes.
            # ------------------------------------------------
            sender.send_state(spatial_state)

            # ------------------------------------------------
            # Draw detection regions
            # ------------------------------------------------
            classifier.draw_regions(
                frame,
                frame_height,
            )

            # Draw every visible detected obstacle
            for detection in tracked_detections:

                if not detection.get(
                    "visible",
                    True,
                ):
                    continue

                x1, y1, x2, y2 = (
                    detection["bbox"]
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )

                label_text = (
                    f"#{detection.get('track_id', '?')} "
                    f"{detection['label']} "
                    f"{detection['confidence']:.2f}"
                )

                cv2.putText(
                    frame,
                    label_text,
                    (
                        x1,
                        max(y1 - 22, 20),
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 0),
                    2,
                )

                classification = (
                    classifier.classify_detection(
                        detection,
                        frame_height,
                    )
                )

                cv2.putText(
                    frame,
                    _format_detection_regions(
                        classification
                    ),
                    (
                        x1,
                        max(y1 - 4, 36),
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                )

            # ------------------------------------------------
            # FPS calculation
            # ------------------------------------------------
            now = time.time()

            fps = (
                1.0 / (now - prev_time)
                if now != prev_time
                else 0.0
            )

            prev_time = now

            # ------------------------------------------------
            # Display occupied regions
            # ------------------------------------------------
            cv2.putText(
                frame,
                "Spatial Occupancy",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2,
            )

            row_y = 72
            row_spacing = 28

            for index, vertical_region in enumerate(
                (
                    "head",
                    "waist",
                    "knee",
                    "ground",
                )
            ):
                row_state = spatial_state[
                    "cells"
                ][vertical_region]

                row_text = (
                    f"{vertical_region.upper():<6} "
                    f"L:{'YES' if row_state['left'] else 'NO '}  "
                    f"C:{'YES' if row_state['center'] else 'NO '}  "
                    f"R:{'YES' if row_state['right'] else 'NO '}"
                )

                cv2.putText(
                    frame,
                    row_text,
                    (
                        20,
                        row_y + index * row_spacing,
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2,
                )

            horizontal_summary_y = (
                row_y
                + 4 * row_spacing
                + 18
            )

            horizontal_text = (
                _format_region_flags(
                    spatial_state["horizontal"],
                    (
                        "left",
                        "center",
                        "right",
                    ),
                    HORIZONTAL_ABBREVIATIONS,
                )
            )

            cv2.putText(
                frame,
                f"HORIZONTAL  {horizontal_text}",
                (
                    20,
                    horizontal_summary_y,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                f"Objects detected: {len(detections)}",
                (
                    20,
                    horizontal_summary_y + 30,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (
                    20,
                    horizontal_summary_y + 60,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                "Status: RUNNING",
                (
                    20,
                    horizontal_summary_y + 90,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2,
            )

            # ------------------------------------------------
            # Display video
            # ------------------------------------------------
            cv2.imshow(
                "Phase 1 - Obstacle Detection",
                frame,
            )

            # ------------------------------------------------
            # Quit with Q
            # ------------------------------------------------
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        # ----------------------------------------------------
        # Cleanup
        # ----------------------------------------------------
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main(