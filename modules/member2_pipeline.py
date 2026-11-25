
import subprocess
import sys

MODULES = [
    ("Object Tracking with ByteTrack", "modules.object_tracking"),
    ("Scene DNA Generation", "modules.scene_dna"),
    ("Movement Trajectory Visualization", "modules.movement_visualization"),
    ("Activity Analytics", "modules.activity_analytics"),
]

def run_pipeline():
    print("\n========== NEMESIS-X | MEMBER 2 PIPELINE ==========\n")

    for title, module in MODULES:
        print(f"\n--- {title} ---")
        subprocess.run(
            [sys.executable, "-m", module],
            check=True
        )

    print("\n========== PIPELINE COMPLETED ==========")
    print("Generated outputs:")
    print("- outputs/tracked_sample.mp4")
    print("- outputs/scene_dna.csv")
    print("- outputs/scene_dna.json")
    print("- outputs/movement_trajectories.png")
    print("- outputs/object_activity.csv")
    print("- outputs/activity_summary.csv")
    print("- data/tracking_history.db")


if __name__ == "__main__":
    run_pipeline()
