# NEMESIS-X
### Open-World Video Intelligence with Temporal, Spatial and Semantic Reasoning

## 1. Project Overview

NEMESIS-X is an AI-powered video intelligence and investigation system designed to help investigators analyze CCTV footage, identify important events, track object movements and explore possible relationships between incidents.

Instead of simply recording video, NEMESIS-X helps transform CCTV footage into structured information that can support faster and more organized investigations.

## 2. Problem Statement

Traditional CCTV surveillance systems mainly record video footage. When an incident occurs, investigators often need to manually review large amounts of footage to understand what happened.

This process can be:
- Time-consuming and difficult.
- Challenging when multiple events occur.
- Difficult when investigators need to connect information from different incidents.
- Dependent on manual observation and analysis.

There is a need for a system that can assist investigators in analyzing video evidence and organizing related information.

## 3. Our Solution

NEMESIS-X combines computer vision, object tracking and event analysis to convert video footage into meaningful investigation information.

The system detects objects, tracks their movements, identifies selected event patterns and stores incident information.

Its Investigation Center allows investigators to organize incidents into cases, examine timelines and explore possible contextual relationships between events.

NEMESIS-X supports human investigation rather than replacing human decision-making.

## 4. Key Features

### 4.1 AI-Powered Video Analysis
- Upload CCTV video footage for analysis.
- Detect objects using YOLO.
- Process video frames using OpenCV.
- Identify and display selected event patterns.

### 4.2 Object Tracking
- Track detected objects across video frames using ByteTrack.
- Maintain object tracking information.
- Analyze movement patterns over time.

### 4.3 Incident Management
- Generate structured incident records.
- Store incident timestamps and event details.
- Maintain incident information for future investigation.

### 4.4 Investigation Center
- Organize multiple incidents into investigation cases.
- Review incident timelines.
- Examine possible relationships between selected incidents.
- View AI-generated analysis and investigation summaries.

### 4.5 Evidence Management
- Maintain references to relevant video evidence.
- Organize evidence associated with incidents.
- Support investigation and report generation.

### 4.6 Visual Analytics
- Display incident information through interactive visualizations.
- Explore event timelines and possible connections.
- Present investigation information in an organized format.

## 5. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| Streamlit | User interface |
| YOLO | Object detection |
| OpenCV | Video processing |
| ByteTrack | Object tracking |
| Supervision | Detection and tracking visualization |
| PyTorch | Deep learning framework |
| SQLite | Incident data storage |
| Pandas | Data handling |
| Plotly | Interactive visualizations |
| NetworkX | Relationship visualization |
| PyAV | Video handling |
| NumPy | Numerical processing |

## 6. System Workflow

1. **Video Input:** The investigator uploads CCTV footage.
2. **Frame Processing:** OpenCV processes the video frames.
3. **Object Detection:** YOLO detects objects in the footage.
4. **Object Tracking:** ByteTrack tracks detected objects across frames.
5. **Event Analysis:** The system analyzes selected movement patterns and event conditions.
6. **Incident Generation:** Important events are stored as structured incident records.
7. **Case Creation:** Investigators organize relevant incidents into investigation cases.
8. **Contextual Analysis:** The system examines available incident information to identify possible relationships.
9. **Investigation Report:** A structured summary helps investigators review timelines, evidence and possible connections.

## 7. Current Implementation

The current prototype includes:

- CCTV video upload and processing.
- YOLO-based object detection.
- ByteTrack-based object tracking.
- Selected event-pattern analysis.
- Structured incident storage.
- Investigation case management.
- Timeline and contextual incident analysis.
- Evidence references and visual reports.

The current contextual correlation uses available incident information and rule-based logic. Identified relationships are possible connections that require human verification.

## 8. Future Scope

- Real-time CCTV stream integration.
- Multi-camera event analysis.
- Improved temporal and spatial reasoning.
- Advanced semantic understanding of video events.
- More sophisticated anomaly detection.
- Better evidence search and retrieval.
- Automated investigation report improvements.
- Integration with larger surveillance environments.

## 9. Target Users

- Law enforcement investigation teams.
- Security and surveillance departments.
- Campus security teams.
- Organizations managing CCTV infrastructure.
- Investigation and forensic analysis teams.

## 10. Project Objective

Our objective is to move beyond traditional CCTV monitoring by developing a system that helps transform video footage into structured, searchable and investigation-oriented information.

**NEMESIS-X — From Watching Footage to Understanding Events.**

## 11. Team Details

**Team Name:** [CORE 4]

**Team Members:**
- [Diya Jain MV]
- [Jyothi N C]
- [Kaneez Fathima U]
- [Madhiya banu Talageri]

---

*Developed as a hackathon project.*
