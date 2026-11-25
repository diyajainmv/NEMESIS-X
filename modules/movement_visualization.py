
import sqlite3
from pathlib import Path

import cv2
import numpy as np
import pandas as pd


DATABASE = "data/tracking_history.db"
OUTPUT_DIR = Path("outputs")


def generate_trajectories():

    if not Path(DATABASE).exists():
        raise FileNotFoundError("Tracking database not found.")

    with sqlite3.connect(DATABASE) as connection:
        history = pd.read_sql_query(
            """
            SELECT track_id, frame_number, center_x, center_y
            FROM observations
            ORDER BY track_id, frame_number
            """,
            connection
        )

    if history.empty:
        print("No tracking history available.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    width = max(800, int(history["center_x"].max()) + 100)
    height = max(600, int(history["center_y"].max()) + 100)

    canvas = np.zeros(
        (height, width, 3),
        dtype=np.uint8
    )

    canvas[:] = (25, 25, 25)

    unique_ids = sorted(history["track_id"].unique())

    for track_id in unique_ids:

        group = history[
            history["track_id"] == track_id
        ].sort_values("frame_number")

        points = [
            (int(row.center_x), int(row.center_y))
            for row in group.itertuples()
        ]

        color = (
            (int(track_id) * 37 + 80) % 255,
            (int(track_id) * 67 + 120) % 255,
            (int(track_id) * 97 + 180) % 255
        )

        for i in range(1, len(points)):
            cv2.line(
                canvas,
                points[i - 1],
                points[i],
                color,
                2
            )

        if points:
            cv2.circle(
                canvas, points[0], 6, (0, 255, 0), -1
            )

            cv2.circle(
                canvas, points[-1], 6, (0, 0, 255), -1
            )

            cv2.putText(
                canvas,
                f"ID {track_id}",
                points[-1],
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

    output_path = OUTPUT_DIR / "movement_trajectories.png"

    cv2.imwrite(str(output_path), canvas)

    print("\nMOVEMENT TRAJECTORY REPORT")
    print("--------------------------")
    print("Tracked objects:", len(unique_ids))

    for track_id in unique_ids:
        count = len(
            history[history["track_id"] == track_id]
        )
        print(f"Object ID {track_id}: {count} observations")

    print("\nTrajectory image saved:", output_path)


if __name__ == "__main__":
    generate_trajectories()
