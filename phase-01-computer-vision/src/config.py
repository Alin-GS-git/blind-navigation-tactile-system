
"""
Phase 1 - Configuration
"""

# ============================================================
# CAMERA SOURCE
# ============================================================

# Mobile phone IP Webcam
CAMERA_SOURCE = "http://192.168.1.65:8080/video"

# To temporarily use the laptop webcam instead:
# CAMERA_SOURCE = 0


# ============================================================
# OBJECT DETECTION
# ============================================================

CONF_THRESHOLD = 0.4


# ============================================================
# SPATIAL CALIBRATION
# ============================================================

# Normalized ratios of frame height. These values define the
# vertical bands used for HEAD / WAIST / KNEE / GROUND.
# Tune them for camera height, mounting angle, and field of view.
VERTICAL_REGION_RATIOS = {
    "head_end": 0.25,
    "waist_end": 0.55,
    "knee_end": 0.80,
}


# ============================================================
# TEMPORAL STABILIZATION / TRACKING
# ============================================================

STABILIZATION_WINDOW = 5
TRACKER_IOU_THRESHOLD = 0.25
TRACKER_MAX_MISSED_FRAMES = 2
