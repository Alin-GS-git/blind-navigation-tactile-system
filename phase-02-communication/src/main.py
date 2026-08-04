"""
Phase 2 - main entry point.

Reuses the Phase 1 pipeline (camera -> detection -> occupancy state)
exactly as it was, and adds one thing: after working out the current
occupancy state, it hands that state to communication.send_state().

main.py contains NO networking code itself - that all lives in
communication.py, per the architecture requirement for this phase.
"""

import os
import sys
import time
import cv2

from config import ESP32_IP, CAMERA_INDEX

# Phase 1's src/ folder is not touched or copied - we just point to it,
# so Phase 1 stays the single source of truth for detection logic.
PHASE1_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "phase-01-computer-vision", "src")
sys.path.insert(0, os.path.abspath(PHASE1_SRC))

from detector import ObstacleDetector      # noqa: E402  (Phase 1, unchanged)
from direction import DirectionClassifier, DirectionStabilizer  # noqa: E402  (Phase 1, unchanged)
from communication import DirectionSender  # Phase 2


def main(camera_index=CAMERA_INDEX, esp32_ip=ESP32_IP, communication_enabled=True):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {camera_index}.")

    detector = ObstacleDetector(conf_threshold=0.4)
    stabilizer = DirectionStabilizer(window_size=5)
    sender = DirectionSender(esp32_ip=esp32_ip, enabled=communication_enabled)

    prev_time = time.time()
    print("Starting Phase 2 (detection + communication). Press 'q' to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Failed to read frame from camera. Stopping.")
            break

        frame_width = frame.shape[1]
        classifier = DirectionClassifier(frame_width)

        # ---- Detection (Phase 1, unchanged) ----
        detections = detector.detect(frame)
        raw_occupied_regions = classifier.get_occupied_regions(detections)
        occupied_regions = stabilizer.update(raw_occupied_regions)

        # ---- Fan-out: Display + Communication ----
        # Display (Phase 1 style overlay)
        classifier.draw_regions(frame)
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{detection['label']} {detection['confidence']:.2f}",
                        (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Communication (Phase 2) - only fires an HTTP request when state changes
        sent = sender.send_state(occupied_regions)
        if sent:
            print(f"[main] Occupancy state changed -> sent {occupied_regions} to ESP32")

        now = time.time()
        fps = 1.0 / (now - prev_time) if now != prev_time else 0.0
        prev_time = now

        cv2.putText(frame, "Occupied Regions", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        cv2.putText(frame, f"LEFT    : {'YES' if occupied_regions['left'] else 'NO'}", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"CENTER  : {'YES' if occupied_regions['center'] else 'NO'}", (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"RIGHT   : {'YES' if occupied_regions['right'] else 'NO'}", (20, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"ESP32: {esp32_ip} {'(on)' if communication_enabled else '(off)'}",
                    (20, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Phase 2 - Detection + Communication", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main(communication_enabled=True)
