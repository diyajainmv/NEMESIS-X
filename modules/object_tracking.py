
import os
import sqlite3
import numpy as np
import supervision as sv

from trackers import ByteTrackTracker


class ObjectTrackingMemory:

    def __init__(self, database_path="data/tracking_history.db"):
        os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)

        self.database_path = database_path

        self.tracker = ByteTrackTracker(
            minimum_consecutive_frames=1
        )

        self.create_database()

    def create_database(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("""
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

            # Safely add class_name to an older database if needed.
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(observations)"
                ).fetchall()
            }

            if "class_name" not in columns:
                connection.execute(
                    "ALTER TABLE observations ADD COLUMN class_name TEXT"
                )

    def process_frame(
        self,
        detections,
        frame_number,
        timestamp=0.0,
        class_names=None
    ):
        tracked = self.tracker.update(
            detections,
            timestamp=float(timestamp)
        )

        if tracked.tracker_id is None:
            return tracked

        rows = []

        for i, track_id in enumerate(tracked.tracker_id):

            if track_id is None or int(track_id) < 0:
                continue

            x1, y1, x2, y2 = tracked.xyxy[i]

            class_id = (
                int(tracked.class_id[i])
                if tracked.class_id is not None else -1
            )

            confidence = (
                float(tracked.confidence[i])
                if tracked.confidence is not None else 0.0
            )

            class_name = "unknown"

            if class_names is not None and class_id >= 0:
                if isinstance(class_names, dict):
                    class_name = str(
                        class_names.get(class_id, "unknown")
                    )
                elif class_id < len(class_names):
                    class_name = str(class_names[class_id])

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            rows.append((
                int(frame_number),
                int(track_id),
                class_id,
                class_name,
                confidence,
                float(x1),
                float(y1),
                float(x2),
                float(y2),
                float(center_x),
                float(center_y),
                float(timestamp)
            ))

        if rows:
            with sqlite3.connect(self.database_path) as connection:
                connection.executemany("""
                    INSERT INTO observations (
                        frame_number,
                        track_id,
                        class_id,
                        class_name,
                        confidence,
                        x1, y1, x2, y2,
                        center_x, center_y,
                        timestamp
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, rows)

        return tracked
