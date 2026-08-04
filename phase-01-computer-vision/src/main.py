"""
Phase 1 - Computer Vision Obstacle Detection
Entry point: opens the camera, runs detection each frame, collects the
occupied LEFT / CENTER / RIGHT regions, and draws everything on screen.

Run with:  python main.py
Quit with: press 'q' in the video window
"""

import time
import cv2

from detector import ObstacleDetector
from direction import DirectionClassifier, DirectionStabilizer


def main(camera_index=0, conf_threshold=0.4):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open camera index {camera_index}. "
            "Check that a camera is connected and not in use by another app."
        )

    detector = ObstacleDetector(conf_threshold=conf_threshold)
    stabilizer = DirectionStabilizer(window_size=5)

    prev_time = time.time()

    print("Starting Phase 1 obstacle detection. Press 'q' to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Failed to read frame from camera. Stopping.")
            break

        frame_height, frame_width = frame.shape[:2]
        classifier = DirectionClassifier(frame_width)

        # Step 5 - detect obstacles in this frame
        detections = detector.detect(frame)

        # Step 6 - inspect every obstacle and merge the occupied regions
        raw_occupied_regions = classifier.get_occupied_regions(detections)

        # Step 10 - stabilize so the output doesn't flicker frame to frame
        occupied_regions = stabilizer.update(raw_occupied_regions)

        # Step 9 - draw everything useful on screen
        classifier.draw_regions(frame)

        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label_text = f"{detection['label']} {detection['confidence']:.2f}"
            cv2.putText(frame, label_text, (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

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
        cv2.putText(frame, f"Objects detected: {len(detections)}", (20, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 190),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "Status: RUNNING", (20, 220),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Phase 1 - Obstacle Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
