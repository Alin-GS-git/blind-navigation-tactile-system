"""
Phase 1 - Computer Vision Obstacle Detection
Entry point: opens the camera, runs detection each frame, selects the
primary obstacle, works out LEFT / CENTER / RIGHT / NO OBSTACLE, and
draws everything on screen.

Run with:  python main.py
Quit with: press 'q' in the video window
"""

import time
import cv2

from detector import ObstacleDetector
from direction import DirectionClassifier, DirectionStabilizer


def select_primary_obstacle(detections, method="largest"):
    """Step 6 - choose which detected obstacle to navigate around.

    method:
        "largest" -> biggest bounding box (used as a simple stand-in
                     for "closest", since a bigger box on a fixed lens
                     usually means the object is nearer the camera)
        "center"  -> object whose center is nearest the middle of frame
    """
    if not detections:
        return None

    if method == "center":
        # picked at call time using the classifier's frame width
        return detections[0]

    return max(detections, key=lambda d: d["area"])


def main(camera_index=0, selection_method="largest", conf_threshold=0.4):
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

        # Step 6 - pick the one obstacle to react to
        if selection_method == "center":
            cx = frame_width / 2
            primary = min(detections, key=lambda d: abs(d["center"][0] - cx)) if detections else None
        else:
            primary = select_primary_obstacle(detections, method=selection_method)

        # Steps 7 & 8 - work out which region the obstacle is in
        raw_direction = classifier.get_direction(primary["center"][0]) if primary else "NO OBSTACLE"

        # Step 10 - stabilize so the output doesn't flicker frame to frame
        direction = stabilizer.update(raw_direction)

        # Step 9 - draw everything useful on screen
        classifier.draw_regions(frame)

        if primary is not None:
            x1, y1, x2, y2 = primary["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label_text = f"{primary['label']} {primary['confidence']:.2f}"
            cv2.putText(frame, label_text, (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        now = time.time()
        fps = 1.0 / (now - prev_time) if now != prev_time else 0.0
        prev_time = now

        cv2.putText(frame, f"Direction: {direction}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        cv2.putText(frame, f"Objects detected: {len(detections)}", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "Status: RUNNING", (20, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Phase 1 - Obstacle Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
