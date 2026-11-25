
import cv2
import torch
from ultralytics import YOLO
from pathlib import Path


class VideoProcessor:
    def __init__(
        self,
        model_path="yolo11n.pt",
        confidence=0.35,
        frame_stride=5
    ):
        self.confidence = confidence
        self.frame_stride = frame_stride

        # Use NVIDIA GPU when available
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
            raise ValueError("Could not open the video file.")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 30.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"Video FPS: {fps}")
        print(f"Total frames: {total_frames}")

        results_data = []
        frame_number = 0

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

                    results_data.append({
                        "frame_number": frame_number,
                        "timestamp": round(timestamp, 3),
                        "detections": detections
                    })

                    print(
                        f"Frame {frame_number} | "
                        f"Time {timestamp:.2f}s | "
                        f"Objects detected: {len(detections)}"
                    )

                frame_number += 1

        finally:
            cap.release()

        print(f"Processing completed. Frames analysed: {len(results_data)}")

        return results_data


if __name__ == "__main__":
    processor = VideoProcessor()

    video_path = input("Enter video path: ").strip().strip('"')

    output = processor.process_video(video_path)

    print("\nSample output:")
    print(output[:2])
