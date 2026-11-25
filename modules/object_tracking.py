
import os
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd
import supervision as sv
from trackers import ByteTrackTracker


class ObjectTrackingMemory:
    def __init__(self, database_path="data/tracking_history.db"):
        os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)

        self.database_path = database_path
        self.tracker = ByteTrackTracker(minimum_consecutive_frames=1)

        self.create_database()

    def create_database(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frame_number INTEGER,
                    track_id INTEGER,
                    class_id INTEGER,
                    confidence REAL,
                    x1 REAL,
                    y1 REAL,
                    x2 REAL,
                    y2 REAL,
                    center_x REAL,
                    center_y REAL,
                    timestamp TEXT
                )
            """)

    def process_frame(self, detections, frame_number):
        """
        Accept detections for one frame and assign tracking IDs.
        detections must be supervision.Detections.
        """

        tracked = self.tracker.update(detections)

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

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            rows.append((
                int(frame_number),
                int(track_id),
                class_id,
                confidence,
                float(x1),
                float(y1),
                float(x2),
                float(y2),
                float(center_x),
                float(center_y),
                datetime.now().isoformat(timespec="seconds")
            ))

        if rows:
            with sqlite3.connect(self.database_path) as connection:
                connection.executemany("""
                    INSERT INTO observations (
                        frame_number, track_id, class_id, confidence,
                        x1, y1, x2, y2, center_x, center_y, timestamp
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, rows)

        return tracked

    def get_history(self, track_id=None):
        query = "SELECT * FROM observations"
        params = ()

        if track_id is not None:
            query += " WHERE track_id = ?"
            params = (int(track_id),)

        query += " ORDER BY frame_number"

        with sqlite3.connect(self.database_path) as connection:
            return pd.read_sql_query(query, connection, params=params)

    def get_movement_summary(self):
        history = self.get_history()

        if history.empty:
            return pd.DataFrame()

        summaries = []

        for track_id, group in history.groupby("track_id"):
            group = group.sort_values("frame_number")

            positions = group[["center_x", "center_y"]].to_numpy()

            if len(positions) > 1:
                distances = np.linalg.norm(
                    np.diff(positions, axis=0), axis=1
                )
                total_distance = float(np.sum(distances))
            else:
                total_distance = 0.0

            summaries.append({
                "track_id": int(track_id),
                "total_observations": len(group),
                "first_frame": int(group["frame_number"].min()),
                "last_frame": int(group["frame_number"].max()),
                "total_movement_pixels": round(total_distance, 2)
            })

        return pd.DataFrame(summaries)


if __name__ == "__main__":
    print("Starting ByteTrack prototype...")

    memory = ObjectTrackingMemory()

    # Synthetic detections for testing.
    # These are sample boxes, NOT real video detections.
    sample_frames = [
        [[50, 50, 100, 120]],
        [[60, 55, 110, 125]],
        [[70, 60, 120, 130]],
    ]

    for frame_number, boxes in enumerate(sample_frames, start=1):
        detections = sv.Detections(
            xyxy=np.array(boxes, dtype=float),
            confidence=np.array([0.95]),
            class_id=np.array([0])
        )

        tracked = memory.process_frame(detections, frame_number)

        print(f"Frame {frame_number}:")
        print("Tracking IDs:", tracked.tracker_id)

    print("\nSaved movement history:")
    print(memory.get_history())

    print("\nMovement statistics:")
    print(memory.get_movement_summary())

    print("\nPrototype completed.")
