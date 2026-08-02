# Phase 2 — Communication (Python ↔ ESP32 over Wi-Fi)

Adds Wi-Fi communication on top of the Phase 1 detection pipeline.
Phase 1's `detector.py` and `direction.py` are unchanged and untouched
by this phase — Phase 2 only adds a `communication.py` module and
wires it into `main.py`.

## Project explanation

Full system flow:

```
Camera
  |
  v
Computer Vision (YOLO)          <- Phase 1, unchanged
  |
  v
Obstacle Detection
  |
  v
Direction (LEFT / CENTER / RIGHT / NONE)
  |
  +----> Display overlay         <- Phase 1, unchanged
  |
  +----> Communication (this phase)
              |
              v
        HTTP GET request
              |
              v
        ESP32 Web Server
              |
              v
        Servo controller          <- Phase 3, not yet built
              |
              v
        Raised tactile pin
```

The ESP32 never performs image processing — all computer vision stays
on the computer. The ESP32 only receives simple commands over HTTP.

## Installation

Phase 2 needs Phase 1's dependencies (for `main.py`, which runs the
camera) plus `requests` and `flask` (for communication + local
testing):

```bash
cd phase-01-computer-vision
pip install -r requirements.txt
cd ../phase-02-communication
pip install -r requirements.txt
```

For the ESP32 side: install Arduino IDE, add the ESP32 board package
(Boards Manager → search "esp32"), and open `esp32/esp32_server.ino`.

## Folder explanation

```
phase-02-communication/
├── src/
│   ├── communication.py   # ALL networking code lives here
│   ├── main.py             # camera + detection + display + communication
│   ├── test_server.py       # mock ESP32 (Flask), for testing without hardware
│   └── test_client.py       # tests communication.py alone, no camera/YOLO
├── esp32/
│   └── esp32_server.ino     # real ESP32 sketch (Arduino IDE)
├── docs/
│   └── testing_procedure.md
└── requirements.txt
```

## Code explanation

**`communication.py`** — `DirectionSender` wraps an ESP32's IP address
and remembers the last direction it sent. `send_direction(direction)`
is a no-op if the direction hasn't changed since the last call;
otherwise it fires one HTTP GET to the matching endpoint (`/left`,
`/center`, `/right`, `/none`). This is the only file in the project
that imports `requests` or knows an IP address exists.

**`main.py`** — Identical to Phase 1's camera loop, with one addition:
after computing the stabilized direction, it calls
`sender.send_direction(direction)`. It contains no HTTP or socket code
itself — all of that is delegated to `communication.py`.

**`test_server.py`** — A tiny Flask app that exposes the same four
endpoints the real ESP32 will expose, and prints whatever it receives.
Lets you test the Python side end-to-end before any ESP32 hardware is
wired up.

**`test_client.py`** — Feeds a hardcoded sequence of directions
(with repeats) into `DirectionSender` and reports how many HTTP
requests actually went out, to verify the "only send on change" rule.

**`esp32/esp32_server.ino`** — Connects to Wi-Fi, starts a `WebServer`
on port 80, and prints `LEFT` / `CENTER` / `RIGHT` / `NONE` to the
Serial Monitor whenever the matching endpoint is hit. No servo code —
that's Phase 3.

## Communication diagram

```
 Python (main.py)                          ESP32
 ─────────────────                         ─────
 direction = "LEFT"
      │
      ▼
 sender.send_direction("LEFT")
      │  (previous was None -> changed)
      ▼
 GET http://<esp32-ip>/left  ─────────────►  handleLeft()
                                                  │
                                                  ▼
                                          Serial.println("LEFT")
                              ◄─────────────  "OK: LEFT"

 direction = "LEFT"   (again, next frame)
      │
      ▼
 sender.send_direction("LEFT")
      │  (previous == "LEFT" -> unchanged)
      ▼
 (nothing sent)
```

## Testing procedure

See [`docs/testing_procedure.md`](docs/testing_procedure.md) for the
three required tests:
1. Python communication test (no YOLO, no ESP32 — uses `test_server.py`)
2. ESP32 communication test (no servos — manual `curl` requests)
3. Integrated test (`test_client.py` talking to the real ESP32)

## Future improvements (Phase 3+)

- Add servo control on the ESP32 side (`/left` etc. move a servo
  instead of only printing).
- Move Wi-Fi credentials out of the `.ino` file and into a
  `secrets.h` that's gitignored.
- Add retry/backoff in `DirectionSender` for flaky Wi-Fi.
- Consider WebSockets instead of HTTP if lower latency is needed.
