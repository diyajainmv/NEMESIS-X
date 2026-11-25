
import cv2
import sqlite3
import numpy as np
import supervision as sv

from pathlib import Path
from trackers import ByteTrackTracker
from modules.video_processing import VideoProcessor


class ObjectTrackingMemory:
    def __init__(self, database_path="data/tracking_history.db"):
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(database_path)
        self.tracker = ByteTrackTracker()
        self.trajectories = {}

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frame_number INTEGER,
                track_id INTEGER,
                class_id INTEGER,
                class_name TEXT,
                confidence REAL,
                x1 REAL,
                y1 REAL,
                x2 REAL,
                y2 REAL,
                center_x REAL,
                center_y REAL,
                timestamp REAL
            )
        """)

        # Add this column if an older prototype database already exists.
        columns = [
            row[1] for row in
            self.connection.execute(
                "PRAGMA table_info(observations)"
            ).fetchall()
        ]

        if "class_name" not in columns:
            self.connection.execute(
                "ALTER TABLE observations ADD COLUMN class_name TEXT"
            )

        self.connection.commit()

    def process_detections(self, frame_data, class_ids):
        detections_data = frame_data["detections"]

        boxes = []
        confidences = []
        classes = []

        for item in detections_data:
            name = item["class_name"]

            if name not in class_ids:
                class_ids[name] = len(class_ids)

            boxes.append(item["bbox"])
            confidences.append(item["confidence"])
            classes.append(class_ids[name])

        if boxes:
            detections = sv.Detections(
                xyxy=np.asarray(boxes, dtype=np.float32),
                confidence=np.asarray(confidences, dtype=np.float32),
                class_id=np.asarray(classes, dtype=int)
            )
        else:
            detections = sv.Detections.empty()

        tracked = self.tracker.update(detections)

        if tracked.tracker_id is None:
            return []

        saved_rows = []

        for i, track_id in enumerate(tracked.tracker_id):
            if track_id < 0:
                continue

            x1, y1, x2, y2 = tracked.xyxy[i]
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            class_id = int(tracked.class_id[i])
            class_name = next(
                name for name, value in class_ids.items()
                if value == class_id
            )

            confidence = float(tracked.confidence[i])

            row = (
                int(frame_data["frame_number"]),
                int(track_id),
                class_id,
                class_name,
                confidence,
                float(x1), float(y1),
                float(x2), float(y2),
                float(center_x), float(center_y),
                float(frame_data["timestamp"])
            )

            saved_rows.append(row)

            self.trajectories.setdefault(int(track_id), []).append(
                (int(center_x), int(center_y))
            )

        self.connection.executemany("""
            INSERT INTO observations (
                frame_number, track_id, class_id, class_name,
                confidence, x1, y1, x2, y2,
                center_x, center_y, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, saved_rows)

        self.connection.commit()
        return saved_rows

    def close(self):
        self.connection.close()


def main():
    video_path = "data/videos/normal/sample.avi"
    output_path = "outputs/tracked_sample.mp4"

    Path("outputs").mkdir(exist_ok=True)

    print("STEP 1: Running YOLO video detection...")
    processor = VideoProcessor()
    frame_results = processor.process_video(video_path)

    print("\nSTEP 2: Starting ByteTrack...")
    memory = ObjectTrackingMemory()
    class_ids = {}

    tracked_frames = {}

    for frame_data in frame_results:
        rows = memory.process_detections(frame_data, class_ids)
        tracked_frames[frame_data["frame_number"]] = rows

        print(
            f"Frame {frame_data['frame_number']} | "
            f"Tracked objects: {len(rows)}"
        )

    print("\nSTEP 3: Creating annotated tracking video...")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        memory.close()
        raise ValueError("Could not reopen input video.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    frame_number = 0
    paths = {}

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            rows = tracked_frames.get(frame_number, [])

            for row in rows:
                (
                    _, track_id, class_id, class_name,
                    confidence, x1, y1, x2, y2,
                    center_x, center_y, timestamp
                ) = row

                x1, y1 = int(x1), int(y1)
                x2, y2 = int(x2), int(y2)
                center = (int(center_x), int(center_y))

                color = (
                    (track_id * 37) % 255,
                    (track_id * 67) % 255,
                    (track_id * 97) % 255
                )

                cv2.rectangle(
                    frame, (x1, y1), (x2, y2), color, 2
                )

                cv2.putText(
                    frame,
                    f"ID {track_id} | {class_name} | {confidence:.2f}",
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    2
                )

                paths.setdefault(track_id, []).append(center)

            for track_id, points in paths.items():
                if len(points) > 1:
                    for i in range(1, len(points)):
                        cv2.line(
                            frame,
                            points[i - 1],
                            points[i],
                            (0, 255, 255),
                            2
                        )

            writer.write(frame)
            frame_number += 1

    finally:
        cap.release()
        writer.release()
        memory.close()

    print("\nTRACKING COMPLETED")
    print(f"Annotated video: {output_path}")
    print("Database: data/tracking_history.db")
    print(f"Unique tracked IDs: {len(paths)}")
    print(f"Frames processed by YOLO: {len(frame_results)}")


if __name__ == "__main__":
    main()
