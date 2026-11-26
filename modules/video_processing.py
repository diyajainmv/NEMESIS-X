
import cv2
import torch
import json
import time
from ultralytics import YOLO
from pathlib import Path


class VideoProcessor:
    def __init__(
        self,
        model_path="yolo11n.pt",
        confidence=0.35,
        frame_stride=5
    ):
        if frame_stride <= 0:
            raise ValueError("frame_stride must be greater than zero")

        self.confidence = confidence
        self.frame_stride = frame_stride
        self.device = 0 if torch.cuda.is_available() else "cpu"

        print(f"Loading YOLO model: {model_path}")
        print(f"Detection device: {self.device}")

        self.model = YOLO(model_path)

    def process_video(self, video_path):
        video_path = str(video_path)

        if not Path(video_path).is_file():
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            cap.release()
            raise ValueError("Could not open the video file.")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 30.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        results_data = []
        frame_number = 0
        total_detections = 0

        frames_dir = Path("data/frames")
        events_dir = Path("data/events")

        frames_dir.mkdir(parents=True, exist_ok=True)
        events_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.perf_counter()

        try:
            while True:
                success, frame = cap.read()

                if not success:
                    break

                if frame_number % self.frame_stride == 0:
                    timestamp = frame_number / fps

                    predictions = self.model.predict(
                        frame,
                        conf=self.confidence,
                        device=self.device,
                        verbose=False
                    )

                    detections = []

                    for result in predictions:
                        for box in result.boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().tolist()

                            detections.append({
                                "class_name": self.model.names[
                                    int(box.cls[0].item())
                                ],
                                "confidence": round(
                                    float(box.conf[0].item()), 4
                                ),
                                "bbox": [
                                    int(x1), int(y1),
                                    int(x2), int(y2)
                                ]
                            })

                    total_detections += len(detections)

                    results_data.append({
                        "frame_number": frame_number,
                        "timestamp": round(timestamp, 3),
                        "detections": detections
                    })

                    # Save YOLO annotated frame
                    annotated_frame = predictions[0].plot()

                    frame_path = frames_dir / (
                        f"frame_{frame_number:06d}.jpg"
                    )

                    if not cv2.imwrite(
                        str(frame_path), annotated_frame
                    ):
                        raise IOError(
                            f"Could not save annotated frame: {frame_path}"
                        )

                    print(
                        f"Frame {frame_number} | "
                        f"Time {timestamp:.2f}s | "
                        f"Objects detected: {len(detections)}"
                    )

                frame_number += 1

        finally:
            cap.release()

        processing_time = time.perf_counter() - start_time

        analysed_frames = len(results_data)
        processing_fps = (
            analysed_frames / processing_time
            if processing_time > 0 else 0
        )

        # Save detection results
        detection_file = events_dir / "detections.json"

        with open(detection_file, "w", encoding="utf-8") as file:
            json.dump(results_data, file, indent=4)

        # Save processing summary
        summary = {
            "video_path": video_path,
            "total_video_frames": total_frames,
            "analysed_frames": analysed_frames,
            "total_detections": total_detections,
            "video_fps": fps,
            "processing_time_seconds": round(processing_time, 3),
            "processing_fps": round(processing_fps, 2)
        }

        summary_file = events_dir / "processing_summary.json"

        with open(summary_file, "w", encoding="utf-8") as file:
            json.dump(summary, file, indent=4)

        print("\nVIDEO PROCESSING COMPLETED")
        print(json.dumps(summary, indent=4))
        print(f"\nDetection JSON: {detection_file}")
        print(f"Processing summary: {summary_file}")
        print(f"Annotated frames: {frames_dir}")

        # Preserve the list return format for Member 2
        return results_data


if __name__ == "__main__":
    processor = VideoProcessor(frame_stride=1)

    video_path = input("Enter video path: ").strip().strip('"')

    output = processor.process_video(video_path)

    print("\nSample output:")
    print(output[:2])
