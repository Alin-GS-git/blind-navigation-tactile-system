"""
Phase 2 - Computer Vision + Wi-Fi Communication

Workflow:

    Mobile/IP Camera
          ↓
    YOLO obstacle detection
          ↓
    3x4 spatial classification
          ↓
    Wi-Fi / HTTP
          ↓
        ESP32
          ↓
    Phase 3 tactile servos

Phase 2 reuses the computer-vision modules from Phase 1.

Run from the project root:

    python phase-02-communication/src/main.py

Or from this directory:

    python main.py

Press 'q' in the camera window to quit.
"""

import sys
import time
import importlib.util
from pathlib import Path

import cv2


# ============================================================
# PROJECT PATHS
# ============================================================

PHASE2_SRC = Path(__file__).resolve().parent

PROJECT_ROOT = PHASE2_SRC.parent.parent

PHASE1_SRC = (
    PROJECT_ROOT
    / "phase-01-computer-vision"
    / "src"
)


# ============================================================
# ADD PHASE 1 AND PHASE 2 TO PYTHON PATH
# ============================================================

if str(PHASE1_SRC) not in sys.path:
    sys.path.insert(0, str(PHASE1_SRC))

if str(PHASE2_SRC) not in sys.path:
    sys.path.insert(0, str(PHASE2_SRC))


# ============================================================
# LOAD A CONFIG FILE DIRECTLY FROM ITS PATH
# ============================================================

def load_config(config_path, module_name):
    """
    Load a config.py directly from its file path.

    This avoids the problem where both Phase 1 and Phase 2
    contain a file called config.py.
    """

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Could not find configuration file:\n"
            f"{config_path}"
        )

    spec = importlib.util.spec_from_file_location(
        module_name,
        config_path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load configuration file:\n"
            f"{config_path}"
        )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


# ============================================================
# LOAD PHASE 1 CONFIG
# ============================================================

PHASE1_CONFIG_PATH = (
    PHASE1_SRC / "config.py"
)

phase1_config = load_config(
    PHASE1_CONFIG_PATH,
    "phase1_config",
)


CAMERA_SOURCE = phase1_config.CAMERA_SOURCE
CONF_THRESHOLD = phase1_config.CONF_THRESHOLD
STABILIZATION_WINDOW = (
    phase1_config.STABILIZATION_WINDOW
)
TRACKER_IOU_THRESHOLD = (
    phase1_config.TRACKER_IOU_THRESHOLD
)
TRACKER_MAX_MISSED_FRAMES = (
    phase1_config.TRACKER_MAX_MISSED_FRAMES
)
VERTICAL_REGION_RATIOS = (
    phase1_config.VERTICAL_REGION_RATIOS
)


# ============================================================
# LOAD PHASE 2 CONFIG
# ============================================================

PHASE2_CONFIG_PATH = (
    PHASE2_SRC / "config.py"
)

phase2_config = load_config(
    PHASE2_CONFIG_PATH,
    "phase2_config",
)


ESP32_IP = phase2_config.ESP32_IP


# ============================================================
# IMPORT PHASE 1 COMPUTER VISION MODULES
# ============================================================

from detector import ObstacleDetector

from direction import (
    DirectionClassifier,
    DirectionStabilizer,
    DetectionTracker,
)


# ============================================================
# IMPORT PHASE 2 COMMUNICATION MODULE
# ============================================================

from communication import DirectionSender


# ============================================================
# DISPLAY ABBREVIATIONS
# ============================================================

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


# ============================================================
# DISPLAY HELPERS
# ============================================================

def _format_region_flags(
    region_state,
    region_order,
    abbreviations,
):
    values = []

    for region in region_order:

        yes_no = (
            "YES"
            if region_state[region]
            else "NO"
        )

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


# ============================================================
# MAIN
# ============================================================

def main(
    camera_source=CAMERA_SOURCE,
    conf_threshold=CONF_THRESHOLD,
    esp32_ip=ESP32_IP,
):

    # --------------------------------------------------------
    # OPEN CAMERA
    # --------------------------------------------------------

    cap = cv2.VideoCapture(
        camera_source
    )

    if not cap.isOpened():

        raise RuntimeError(
            f"Could not open camera source:\n"
            f"{camera_source}\n\n"
            "Check that the mobile IP Webcam server "
            "is running and that the phone and laptop "
            "are connected to the same network."
        )

    # Reduce buffering for network camera streams.

    if isinstance(camera_source, str):

        cap.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1,
        )


    # --------------------------------------------------------
    # INITIALIZE PHASE 1
    # --------------------------------------------------------

    detector = ObstacleDetector(
        conf_threshold=conf_threshold
    )

    stabilizer = DirectionStabilizer(
        window_size=STABILIZATION_WINDOW
    )

    tracker = DetectionTracker(
        iou_threshold=TRACKER_IOU_THRESHOLD,
        max_missed_frames=(
            TRACKER_MAX_MISSED_FRAMES
        ),
    )


    # --------------------------------------------------------
    # INITIALIZE PHASE 2 COMMUNICATION
    # --------------------------------------------------------

    sender = DirectionSender(
        esp32_ip=esp32_ip,
        enabled=True,
    )


    # --------------------------------------------------------
    # STARTUP INFORMATION
    # --------------------------------------------------------

    prev_time = time.time()

    print()
    print("=" * 65)
    print("PHASE 2 - COMPUTER VISION + ESP32 COMMUNICATION")
    print("=" * 65)

    print(
        f"Camera source : {camera_source}"
    )

    print(
        f"ESP32 IP      : {esp32_ip}"
    )

    print()

    print(
        "Workflow:"
    )

    print(
        "Camera -> YOLO -> 3x4 spatial state "
        "-> Wi-Fi -> ESP32"
    )

    print()

    print(
        "3x4 spatial matrix:"
    )

    print(
        "HEAD   : LEFT / CENTER / RIGHT"
    )

    print(
        "WAIST  : LEFT / CENTER / RIGHT"
    )

    print(
        "KNEE   : LEFT / CENTER / RIGHT"
    )

    print(
        "GROUND : LEFT / CENTER / RIGHT"
    )

    print()

    print(
        "Press 'q' in the camera window to quit."
    )

    print("=" * 65)
    print()


    # ========================================================
    # MAIN LOOP
    # ========================================================

    while True:

        # ----------------------------------------------------
        # READ CAMERA FRAME
        # ----------------------------------------------------

        ok, frame = cap.read()

        if not ok:

            print(
                "[main] Failed to read frame "
                "from camera. Stopping."
            )

            break


        frame_height, frame_width = (
            frame.shape[:2]
        )


        # ----------------------------------------------------
        # CREATE CLASSIFIER
        # ----------------------------------------------------

        classifier = DirectionClassifier(
            frame_width,
            vertical_ratios=(
                VERTICAL_REGION_RATIOS
            ),
        )


        # ----------------------------------------------------
        # YOLO DETECTION
        # ----------------------------------------------------

        detections = detector.detect(
            frame
        )


        # ----------------------------------------------------
        # TRACK DETECTIONS
        # ----------------------------------------------------

        tracked_detections = tracker.update(
            detections
        )


        # ----------------------------------------------------
        # CREATE 3x4 SPATIAL STATE
        # ----------------------------------------------------

        raw_spatial_state = (
            classifier.get_spatial_state(
                tracked_detections,
                frame_height,
            )
        )


        # ----------------------------------------------------
        # STABILIZE STATE
        # ----------------------------------------------------

        spatial_state = stabilizer.update(
            raw_spatial_state
        )


        # ----------------------------------------------------
        # SEND STATE TO ESP32
        # ----------------------------------------------------

        sender.send_state(
            spatial_state
        )


        # ----------------------------------------------------
        # DRAW SPATIAL REGIONS
        # ----------------------------------------------------

        classifier.draw_regions(
            frame,
            frame_height,
        )


        # ----------------------------------------------------
        # DRAW DETECTED OBJECTS
        # ----------------------------------------------------

        for detection in tracked_detections:

            if not detection.get(
                "visible",
                True,
            ):
                continue


            x1, y1, x2, y2 = (
                detection["bbox"]
            )


            # Bounding box

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2,
            )


            # Object label

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
                    max(
                        y1 - 22,
                        20,
                    ),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
            )


            # Determine the spatial location
            # of this particular detection.

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
                    max(
                        y1 - 4,
                        36,
                    ),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
            )


        # ----------------------------------------------------
        # FPS
        # ----------------------------------------------------

        now = time.time()

        fps = (
            1.0 / (now - prev_time)
            if now != prev_time
            else 0.0
        )

        prev_time = now


        # ====================================================
        # DISPLAY 3x4 MATRIX
        # ====================================================

        cv2.putText(
            frame,
            "3x4 Spatial Occupancy",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
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

            row_state = (
                spatial_state["cells"][
                    vertical_region
                ]
            )


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
                    row_y
                    + index * row_spacing,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )


        # ----------------------------------------------------
        # HORIZONTAL SUMMARY
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # OBJECT COUNT
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # FPS
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # ESP32 STATUS
        # ----------------------------------------------------

        cv2.putText(
            frame,
            f"ESP32: {esp32_ip}",
            (
                20,
                horizontal_summary_y + 90,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 0),
            2,
        )


        # ----------------------------------------------------
        # SHOW CAMERA
        # ----------------------------------------------------

        cv2.imshow(
            "Phase 2 - Obstacle Detection + ESP32",
            frame,
        )


        # ----------------------------------------------------
        # QUIT
        # ----------------------------------------------------

        if (
            cv2.waitKey(1) & 0xFF
            == ord("q")
        ):
            break


    # ========================================================
    # CLEANUP
    # ========================================================

    cap.release()

    cv2.destroyAllWindows()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()