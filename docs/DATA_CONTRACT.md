# NEMESIS-X – Common Data Format

All four modules must follow this format so they can work together.

## 1. Video Processing Output

Member 1 sends:

```json
{
  "frame_number": 25,
  "timestamp": 2.5,
  "detections": [
    {
      "class_name": "person",
      "confidence": 0.92,
      "bbox": [100, 120, 250, 400]
    }
  ]
}
```

## 2. Object Tracking Output

Member 2 adds tracking information:

```json
{
  "frame_number": 25,
  "timestamp": 2.5,
  "tracked_objects": [
    {
      "track_id": 1,
      "class_name": "person",
      "bbox": [100, 120, 250, 400],
      "center": [175, 260]
    }
  ]
}
```

## 3. Event Intelligence Output

Member 3 sends:

```json
{
  "event_id": "EVT001",
  "event_type": "unattended_object",
  "timestamp": 15.5,
  "track_ids": [1, 2],
  "anomaly_score": 0.85,
  "explanation": "An object remained stationary after a person moved away.",
  "evidence_frames": [150, 180, 210]
}
```

## 4. Dashboard Input

Member 4 displays:

- Event ID
- Event type
- Camera/location
- Timestamp
- Anomaly score
- Explanation
- Evidence frames
- Incident status

## Important Rules

1. Do not change the agreed field names without informing the team.
2. All timestamps must be in seconds from the beginning of the video.
3. Bounding boxes use `[x1, y1, x2, y2]`.
4. Anomaly scores must be between 0 and 1.
5. Events are potential anomalies and require human verification.