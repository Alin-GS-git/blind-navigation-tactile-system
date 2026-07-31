"""
Step 5 - Object detection.

Wraps a YOLOv8 model (via the `ultralytics` package) and returns a clean
list of detections: label, confidence, bounding box, center point, and
area. Filtering to a fixed set of "obstacle-like" labels helps satisfy
Step 10 (reduce false detections / ignore insignificant objects) by
ignoring classes that aren't relevant obstacles (e.g. a detected tie or
cell phone shouldn't trigger navigation).
"""

from ultralytics import YOLO

# Labels from the standard COCO dataset (what yolov8n.pt is trained on)
# that correspond to obstacles named in the roadmap (people, chairs,
# tables, boxes/bags). Add or remove labels here to tune behavior.
RELEVANT_LABELS = {
    "person",
    "chair",
    "couch",
    "dining table",
    "bed",
    "suitcase",
    "backpack",
    "handbag",
    "bench",
}


class ObstacleDetector:
    def __init__(self, model_path="yolov8n.pt", conf_threshold=0.4, filter_labels=True):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.filter_labels = filter_labels

    def detect(self, frame):
        results = self.model(frame, verbose=False)[0]
        detections = []

        for box in results.boxes:
            conf = float(box.conf[0])
            if conf < self.conf_threshold:
                continue

            cls_id = int(box.cls[0])
            label = self.model.names[cls_id]

            if self.filter_labels and label not in RELEVANT_LABELS:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            area = max(0, (x2 - x1)) * max(0, (y2 - y1))

            detections.append({
                "label": label,
                "confidence": conf,
                "bbox": (x1, y1, x2, y2),
                "center": center,
                "area": area,
            })

        return detections
