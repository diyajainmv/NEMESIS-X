
import json
import uuid
from pathlib import Path

import cv2
import numpy as np
import supervision as sv

from modules.video_processing import VideoProcessor
from modules.object_tracking import ObjectTrackingMemory
from modules.event_intelligence import (
    _read_sqlite,
    analyze_frames,
    create_event_graph,
)


BASE_DIR = Path(__file__).resolve().parent.parent


def run_video_analysis(
    video_path,
    progress_callback=None,
    frame_callback=None,
):
    run_id = uuid.uuid4().hex[:10]

    db_path = BASE_DIR / "data" / "events" / f"tracking_{run_id}.db"
    events_path = BASE_DIR / "data" / "events" / f"events_{run_id}.json"
    annotated_dir = BASE_DIR / "data" / "outputs" / run_id

    db_path.parent.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)

    def report(value, message):
        if progress_callback:
            progress_callback(value, message)

    report(5, "Loading YOLO model...")

    processor = VideoProcessor(frame_stride=1)

    report(10, "Running YOLO detection...")
    detections_data = processor.process_video(str(video_path))

    if not detections_data:
        raise ValueError("No video frames or detections were returned.")

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError("Could not reopen the video for tracking visualization.")

    fps = cap.get(cv2.CAP_PROP_FPS)

    if not fps or fps <= 0:
        cap.release()
        raise ValueError("Could not determine video FPS.")

    model_names = processor.model.names
    tracker = ObjectTrackingMemory(str(db_path))

    report(65, "Running ByteTrack and creating annotated frames...")

    total_frames = len(detections_data)
    frames_annotated = 0

    try:
        for index, frame_data in enumerate(detections_data):

            ret, frame = cap.read()

            if not ret:
                break

            frame_number = int(frame_data["frame_number"])
            timestamp = float(
                frame_data.get("timestamp", frame_number / fps)
            )

            boxes = []
            confidences = []
            class_ids = []

            for detection in frame_data.get("detections", []):

                bbox = detection["bbox"]
                class_name = detection["class_name"]

                if isinstance(model_names, dict):
                    matching_ids = [
                        int(k)
                        for k, v in model_names.items()
                        if v == class_name
                    ]
                else:
                    matching_ids = [
                        i
                        for i, v in enumerate(model_names)
                        if v == class_name
                    ]

                if not matching_ids:
                    continue

                boxes.append(bbox)
                confidences.append(float(detection["confidence"]))
                class_ids.append(matching_ids[0])

            sv_detections = sv.Detections(
                xyxy=np.asarray(boxes, dtype=float).reshape(-1, 4),
                confidence=np.asarray(confidences, dtype=float),
                class_id=np.asarray(class_ids, dtype=int),
            )

            tracked = tracker.process_frame(
                sv_detections,
                frame_number,
                timestamp=timestamp,
                class_names=model_names,
            )

            # Draw YOLO bounding boxes and ByteTrack IDs.
            if tracked.tracker_id is not None:

                for i, track_id in enumerate(tracked.tracker_id):

                    if track_id is None or int(track_id) < 0:
                        continue

                    x1, y1, x2, y2 = map(
                        int, tracked.xyxy[i]
                    )

                    class_id = (
                        int(tracked.class_id[i])
                        if tracked.class_id is not None
                        else -1
                    )

                    if isinstance(model_names, dict):
                        class_name = model_names.get(
                            class_id, "object"
                        )
                    elif 0 <= class_id < len(model_names):
                        class_name = model_names[class_id]
                    else:
                        class_name = "object"

                    confidence = (
                        float(tracked.confidence[i])
                        if tracked.confidence is not None
                        else 0.0
                    )

                    label = (
                        f"{class_name} | ID: {int(track_id)} "
                        f"| {confidence:.2f}"
                    )

                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2,
                    )

                    text_y = max(y1 - 10, 20)

                    cv2.putText(
                        frame,
                        label,
                        (x1, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 0),
                        2,
                    )

            # Save the annotated frame for this analysis run.
            frame_path = (
                annotated_dir / f"frame_{frame_number:06d}.jpg"
            )

            cv2.imwrite(str(frame_path), frame)
            frames_annotated += 1

            # Send periodic frames to Streamlit.
            if frame_callback and (
                index % 5 == 0 or index == total_frames - 1
            ):
                frame_rgb = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB,
                )

                frame_callback(
                    frame_rgb,
                    frame_number,
                    timestamp,
                )

            if index % 10 == 0 or index == total_frames - 1:
                progress = 65 + int(
                    20 * (index + 1) / total_frames
                )

                report(
                    progress,
                    f"ByteTrack processing frame "
                    f"{index + 1}/{total_frames}",
                )

    finally:
        cap.release()

    report(88, "Generating event intelligence...")

    frames = _read_sqlite(str(db_path))

    events, analysis = analyze_frames(frames)

    graph = create_event_graph(events)

    output = {
        "run_id": run_id,
        "events": events,
        "event_graph": {
            "nodes": [
                {"event_id": node, **attributes}
                for node, attributes in graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    **attributes,
                }
                for source, target, attributes in graph.edges(data=True)
            ],
        },
        "analysis": analysis,
    }

    with open(events_path, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    report(100, "Analysis completed.")

    return {
        "run_id": run_id,
        "database_path": str(db_path),
        "events_path": str(events_path),
        "annotated_dir": str(annotated_dir),
        "frames_processed": len(frames),
        "frames_annotated": frames_annotated,
        "events": events,
        "analysis": analysis,
    }
