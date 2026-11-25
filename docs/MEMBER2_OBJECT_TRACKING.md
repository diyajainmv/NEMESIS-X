

\# NEMESIS-X — Member 2: Object Tracking \& Scene DNA



\## 1. Module Overview



The Object Tracking and Scene DNA module identifies detected objects, maintains their tracking identities across video frames, records their movement history, and generates activity analytics.



\## 2. Technologies Used



\- Python — Core implementation

\- YOLO (Ultralytics) — Object detection

\- ByteTrack — Multi-object tracking

\- OpenCV — Video processing and visualization

\- Supervision — Detection data handling

\- NumPy — Coordinate and movement calculations

\- Pandas — Activity data analysis

\- SQLite — Tracking history storage



\## 3. System Workflow



1\. Video Input — Receives the input video.

2\. Object Detection — YOLO identifies objects and their bounding boxes.

3\. Object Tracking — ByteTrack maintains tracking IDs across frames.

4\. Coordinate Extraction — Records bounding boxes and object centre coordinates.

5\. Database Storage — Saves observations, frame numbers, timestamps and tracking IDs in SQLite.

6\. Scene DNA — Generates time-based object movement records.

7\. Movement Visualization — Displays object trajectories.

8\. Activity Analytics — Calculates movement distance, direction, speed and activity status.



\## 4. Main Modules



| File | Responsibility |

|---|---|

| video\_processing.py | Video ingestion and YOLO detection |

| object\_tracking.py | ByteTrack integration and tracking history |

| scene\_dna.py | Time-based object movement records |

| movement\_visualization.py | Object trajectory visualization |

| activity\_analytics.py | Movement and activity analysis |

| member2\_pipeline.py | Runs the complete Member 2 workflow |



\## 5. Generated Outputs



\- tracked\_sample.mp4 — Video with bounding boxes and tracking IDs

\- scene\_dna.csv — Object movement records

\- scene\_dna.json — Structured Scene DNA records

\- movement\_trajectories.png — Object movement paths

\- object\_activity.csv — Per-object activity records

\- activity\_summary.csv — Aggregated activity statistics

\- tracking\_history.db — SQLite tracking database



\## 6. Scene DNA Parameters



The system records:



\- Tracking ID

\- Object class

\- First and last observed frame

\- Observation count

\- Movement distance

\- Net displacement

\- Movement direction

\- Observation duration

\- Average pixel speed

\- Moving or stationary status



\## 7. Current Prototype Scope



The current prototype is demonstrated using a sample video and YOLO-based object detection.



Frames are analysed at a configured frame stride. Movement measurements are calculated in image pixels and are not real-world physical distances.



The current implementation demonstrates offline video processing. Live CCTV integration and real-world calibrated movement measurements are outside this prototype's current scope.



\## 8. Execution



Run the complete Member 2 pipeline from the project root:



&#x20;   python -m modules.member2\_pipeline



\## 9. Expected Result



The pipeline generates an annotated tracking video, object movement records, trajectory visualization, activity analytics and a SQLite database.



This provides a structured movement-history layer for the NEMESIS-X system.



