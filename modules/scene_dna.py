
import sqlite3
import json
from pathlib import Path

import numpy as np
import pandas as pd


DATABASE = "data/tracking_history.db"
OUTPUT_DIR = Path("outputs")


def calculate_direction(dx, dy):
    if np.hypot(dx, dy) < 5:
        return "Stationary"

    angle = np.degrees(np.arctan2(-dy, dx)) % 360

    directions = [
        "East", "North-East", "North", "North-West",
        "West", "South-West", "South", "South-East"
    ]

    index = int((angle + 22.5) // 45) % 8
    return directions[index]


def calculate_duration(timestamps):
    values = pd.to_numeric(
        timestamps, errors="coerce"
    )

    if values.notna().all():
        return max(0.0, float(values.max() - values.min()))

    dates = pd.to_datetime(
        timestamps, errors="coerce", utc=True
    ).dropna()

    if len(dates) >= 2:
        return max(
            0.0,
            (dates.max() - dates.min()).total_seconds()
        )

    return 0.0


def generate_scene_dna():
    if not Path(DATABASE).exists():
        raise FileNotFoundError(
            f"Tracking database not found: {DATABASE}"
        )

    with sqlite3.connect(DATABASE) as connection:
        history = pd.read_sql_query(
            "SELECT * FROM observations",
            connection
        )

    if history.empty:
        print("No tracking observations found.")
        return

    required = {
        "track_id", "frame_number", "center_x",
        "center_y", "timestamp"
    }

    missing = required - set(history.columns)

    if missing:
        raise ValueError(
            f"Missing database columns: {missing}"
        )

    results = []

    for track_id, group in history.groupby("track_id"):
        group = group.sort_values("frame_number")

        positions = group[
            ["center_x", "center_y"]
        ].to_numpy(dtype=float)

        if len(positions) > 1:
            movements = np.diff(positions, axis=0)

            distances = np.linalg.norm(
                movements, axis=1
            )

            total_distance = float(distances.sum())

            dx = float(
                positions[-1][0] - positions[0][0]
            )

            dy = float(
                positions[-1][1] - positions[0][1]
            )
        else:
            total_distance = 0.0
            dx = 0.0
            dy = 0.0

        net_displacement = float(np.hypot(dx, dy))

        direction = calculate_direction(dx, dy)

        duration = calculate_duration(group["timestamp"])

        average_speed = (
            total_distance / duration
            if duration > 0 else 0.0
        )

        activity = (
            "Stationary"
            if total_distance < 5
            else "Moving"
        )

        class_name = (
            group["class_name"].iloc[0]
            if "class_name" in group.columns
            else str(group["class_id"].iloc[0])
            if "class_id" in group.columns
            else "Unknown"
        )

        results.append({
            "track_id": int(track_id),
            "object_class": str(class_name),
            "total_observations": int(len(group)),
            "first_frame": int(group["frame_number"].min()),
            "last_frame": int(group["frame_number"].max()),
            "total_movement_pixels": round(total_distance, 2),
            "net_displacement_pixels": round(
                net_displacement, 2
            ),
            "movement_direction": direction,
            "duration_seconds": round(duration, 2),
            "average_speed_pixels_per_second": round(
                average_speed, 2
            ),
            "activity_status": activity
        })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = pd.DataFrame(results)

    csv_path = OUTPUT_DIR / "scene_dna.csv"
    json_path = OUTPUT_DIR / "scene_dna.json"

    report.to_csv(csv_path, index=False)

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            indent=4
        )

    print("\n========== SCENE DNA REPORT ==========")
    print(report.to_string(index=False))

    print("\nScene DNA generation completed.")
    print(f"CSV report: {csv_path}")
    print(f"JSON report: {json_path}")


if __name__ == "__main__":
    generate_scene_dna()
