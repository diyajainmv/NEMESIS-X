
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


DATABASE = "data/tracking_history.db"
OUTPUT_DIR = Path("outputs")

MOVEMENT_THRESHOLD = 5.0


def convert_timestamp(value):
    """Convert numeric or date-based timestamps into seconds."""
    if pd.isna(value):
        return np.nan

    try:
        return float(value)
    except (ValueError, TypeError):
        parsed = pd.to_datetime(
            value, errors="coerce", utc=True
        )

        if pd.isna(parsed):
            return np.nan

        return parsed.timestamp()


def get_direction(dx, dy):
    if np.hypot(dx, dy) < MOVEMENT_THRESHOLD:
        return "Stationary"

    angle = np.degrees(np.arctan2(-dy, dx)) % 360

    directions = [
        "East", "North-East", "North", "North-West",
        "West", "South-West", "South", "South-East"
    ]

    index = int((angle + 22.5) // 45) % 8

    return directions[index]


def generate_activity_analytics():

    if not Path(DATABASE).exists():
        raise FileNotFoundError(
            "Tracking database not found."
        )

    with sqlite3.connect(DATABASE) as connection:
        history = pd.read_sql_query(
            """
            SELECT track_id, frame_number,
                   center_x, center_y, timestamp
            FROM observations
            ORDER BY track_id, frame_number
            """,
            connection
        )

    if history.empty:
        print("No tracking observations available.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    history["time_seconds"] = history[
        "timestamp"
    ].apply(convert_timestamp)

    activity_records = []
    summaries = []

    for track_id, group in history.groupby("track_id"):

        group = group.sort_values("frame_number").reset_index(
            drop=True
        )

        positions = group[
            ["center_x", "center_y"]
        ].to_numpy(dtype=float)

        moving_count = 0
        stationary_count = 0
        total_distance = 0.0
        direction_changes = 0
        previous_direction = None

        for i in range(len(group)):

            if i == 0:
                dx = 0.0
                dy = 0.0
                distance = 0.0
                duration = 0.0
                direction = "Unknown"
                status = "Unknown"

            else:
                dx = positions[i][0] - positions[i - 1][0]
                dy = positions[i][1] - positions[i - 1][1]

                distance = float(np.hypot(dx, dy))
                total_distance += distance

                current_time = group.loc[i, "time_seconds"]
                previous_time = group.loc[i - 1, "time_seconds"]

                if (
                    pd.notna(current_time)
                    and pd.notna(previous_time)
                    and current_time > previous_time
                ):
                    duration = float(
                        current_time - previous_time
                    )
                else:
                    duration = 0.0

                direction = get_direction(dx, dy)

                if distance >= MOVEMENT_THRESHOLD:
                    status = "Moving"
                    moving_count += 1
                else:
                    status = "Stationary"
                    stationary_count += 1

                if direction != "Stationary":
                    if (
                        previous_direction is not None
                        and direction != previous_direction
                    ):
                        direction_changes += 1

                    previous_direction = direction

            speed = (
                distance / duration
                if duration > 0 else 0.0
            )

            activity_records.append({
                "track_id": int(track_id),
                "frame_number": int(
                    group.loc[i, "frame_number"]
                ),
                "movement_distance": round(distance, 2),
                "direction": direction,
                "speed_pixels_per_second": round(speed, 2),
                "activity_status": status
            })

        valid_count = moving_count + stationary_count

        moving_percentage = (
            moving_count / valid_count * 100
            if valid_count else 0.0
        )

        summaries.append({
            "track_id": int(track_id),
            "total_observations": len(group),
            "moving_observations": moving_count,
            "stationary_observations": stationary_count,
            "moving_percentage": round(moving_percentage, 2),
            "direction_changes": direction_changes,
            "total_distance_pixels": round(total_distance, 2)
        })

    activity_df = pd.DataFrame(activity_records)
    summary_df = pd.DataFrame(summaries)

    activity_path = OUTPUT_DIR / "object_activity.csv"
    summary_path = OUTPUT_DIR / "activity_summary.csv"

    activity_df.to_csv(activity_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print("\n========== OBJECT ACTIVITY ANALYTICS ==========")
    print(summary_df.to_string(index=False))

    print("\nActivity records:")
    print(activity_df.head(10).to_string(index=False))

    print("\nAnalytics completed successfully.")
    print("Activity records:", activity_path)
    print("Activity summary:", summary_path)


if __name__ == "__main__":
    generate_activity_analytics()
