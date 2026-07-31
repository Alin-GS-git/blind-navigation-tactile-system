# Phase 1 — Computer Vision Obstacle Detection

A camera-based system that detects obstacles and reports whether they
are on the **LEFT**, **CENTER**, or **RIGHT** of the user's path (or
**NO OBSTACLE**). This phase runs entirely on a laptop with Python —
no ESP32 or other hardware required.

## How the roadmap maps to this code

| Roadmap step | Where it lives |
|---|---|
| Step 1 — Define objective | This README |
| Step 2 — Choose platform | Laptop + Python (this repo) |
| Step 3 — Set up environment | `requirements.txt`, instructions below |
| Step 4 — Access the camera | `main.py` (`cv2.VideoCapture`) |
| Step 5 — Object detection | `detector.py` (YOLOv8 via `ultralytics`) |
| Step 6 — Select primary obstacle | `main.py` → `select_primary_obstacle()` |
| Step 7 — Divide camera view | `direction.py` → `DirectionClassifier` |
| Step 8 — Determine direction | `direction.py` → `get_direction()` |
| Step 9 — Display results overlay | `main.py` (bounding box, label, confidence, direction, status) |
| Step 10 — Improve stability | `detector.py` label filtering + `direction.py` → `DirectionStabilizer` |
| Step 11 — Test scenarios | `docs/testing_log.md` |
| Step 12 — Final validation | Checklist below |

## Setup (Step 3)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The first run will auto-download the small YOLOv8 model weights
(`yolov8n.pt`), so you'll need an internet connection once.

## Run (Steps 4–9)

```bash
python main.py
```

- A window opens showing the live camera feed.
- Detected obstacles are boxed with their label and confidence.
- Two vertical guide lines mark the LEFT / CENTER / RIGHT regions.
- The current direction, object count, FPS, and status are overlaid.
- Press `q` to quit.

### Choosing how the primary obstacle is picked (Step 6)

In `main()`, change `selection_method`:
- `"largest"` (default) — treats the biggest bounding box as nearest.
- `"center"` — picks whichever obstacle is closest to the middle of frame.

## Testing (Step 11)

Use `docs/testing_log.md` to record results across scenarios: single
obstacle, multiple obstacles, moving obstacles, different lighting,
different backgrounds, and different indoor environments.

## Step 12 — Final validation checklist

- [ ] Live camera feed runs smoothly
- [ ] Obstacles are detected with bounding boxes and labels
- [ ] Frame is divided into LEFT / CENTER / RIGHT
- [ ] Correct direction output for each region
- [ ] Output is stable (no rapid flicker between directions)
- [ ] Tested under multiple scenarios (see testing log)
- [ ] Runs with no ESP32/hardware dependency

## Project structure

```
obstacle-detection-phase1/
├── main.py            # camera loop, obstacle selection, overlay
├── detector.py         # YOLOv8 wrapper + label filtering
├── direction.py         # region division + direction stabilizer
├── requirements.txt
├── docs/
│   └── testing_log.md
└── .gitignore
```

## Next phase

Phase 2 will connect this direction output (LEFT/CENTER/RIGHT/NO
OBSTACLE) to the ESP32 hardware for physical feedback.
