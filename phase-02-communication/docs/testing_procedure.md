# Phase 2 — Testing Procedure

Three tests, matching the roadmap's testing requirement.

## Test 1 — Python communication test (no YOLO, no ESP32)

Confirms `DirectionSender` only fires a request when direction changes.

Terminal A:
```bash
cd phase-02-communication/src
python test_server.py
```

Terminal B:
```bash
cd phase-02-communication/src
python test_client.py
```

**Expected:** `test_client.py` "detects" 8 directions but only 3 are new
(LEFT, CENTER, RIGHT) - the server should print exactly those 3 lines,
and the client should report "Total requests sent: 3".

## Test 2 — ESP32 communication test (no servos)

Confirms the real ESP32 receives and prints requests correctly.

1. Flash `esp32/esp32_server.ino` to the ESP32 via Arduino IDE.
2. Open Serial Monitor at 115200 baud.
3. Note the printed IP address.
4. From a browser or `curl`, hit each endpoint manually:
   ```bash
   curl http://<esp32-ip>/left
   curl http://<esp32-ip>/center
   curl http://<esp32-ip>/right
   curl http://<esp32-ip>/none
   ```
**Expected:** Serial Monitor prints `LEFT`, `CENTER`, `RIGHT`, `NONE`
respectively, one per request.

## Test 3 — Integrated communication test

Confirms the full Python -> ESP32 path with the real device.

1. Flash and power on the ESP32 (Test 2), note its IP.
2. Edit `test_client.py` (or `main.py`) to use that IP and port 80
   instead of the mock server:
   ```python
   sender = DirectionSender(esp32_ip="<esp32-ip>", port=80, enabled=True)
   ```
3. Run `python test_client.py`.

**Expected:** Serial Monitor on the ESP32 prints `LEFT`, `CENTER`,
`RIGHT` — matching what the client sent, with no duplicate prints for
repeated directions.

Once Test 3 passes, `main.py` can be run with the camera for the full
detection + communication pipeline.
