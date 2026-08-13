"""
Phase 2 - Communication Configuration

Phase 2 uses the same camera source as Phase 1, performs the
same 3x4 spatial detection, and sends the resulting spatial
state to the ESP32 over Wi-Fi.
"""

# ============================================================
# ESP32 NETWORK CONFIGURATION
# ============================================================

# Replace this with the IP address printed by esp32_server.ino
# in the ESP32 Serial Monitor.
ESP32_IP = "192.168.137.15"

ESP32_PORT = 80


# ============================================================
# CAMERA CONFIGURATION
# ============================================================

# Use the same mobile IP Webcam source as Phase 1.
#
# IMPORTANT:
# Keep this synchronized with:
#
# phase-01-computer-vision/src/config.py
#
CAMERA_SOURCE = "http://192.168.91.214:8080/video"


# ============================================================
# COMMUNICATION CONFIGURATION
# ============================================================

# Maximum time to wait for an ESP32 HTTP response.
REQUEST_TIMEOUT = 1


# ============================================================
# TEST SERVER CONFIGURATION
# ============================================================

# Port used by test_server.py.
TEST_SERVER_PORT = 5000