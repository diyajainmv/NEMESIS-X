# NEMESIS-X
### Open-World Video Intelligence with Temporal, Spatial and Semantic Reasoning

## 1. Project Overview

NEMESIS-X is an AI-powered video intelligence platform designed to help security teams analyze CCTV footage and investigate potentially suspicious activities.

It processes video footage, tracks object movements, analyzes event patterns, and organizes incidents into investigation cases.

## 2. Problem Statement

Traditional CCTV systems mainly record surveillance footage. Security personnel often need to manually review long recordings to identify suspicious activities and understand how different incidents may be connected.

This process is time-consuming and important information can be overlooked.

## 3. Proposed Solution

NEMESIS-X transforms CCTV footage into structured and explainable investigation information.

Key capabilities:
- Object detection in uploaded CCTV videos.
- Object tracking and movement history.
- Event and interaction analysis.
- Incident record creation.
- Investigation case management.
- Contextual correlation of multiple incidents.
- Investigation reports with timelines and evidence.

## 4. Key Features

### Video Analysis
Processes uploaded CCTV footage and detects objects using computer vision.

### Object Tracking
Tracks detected objects across video frames using ByteTrack.

### Event Intelligence
Analyzes movement patterns, object interactions and potentially unusual activities.

### Incident Management
Stores and manages incidents with timestamps, explanations and evidence references.

### Investigation Center
Allows investigators to group multiple incidents into cases and examine possible contextual relationships.

### Investigation Reports
Generates structured reports containing event timelines, possible connections, anomaly information and recommendations for human verification.

## 5. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Web interface |
| YOLO | Object detection |
| OpenCV | Video processing |
| ByteTrack | Object tracking |
| Supervision | Detection and tracking visualization |
| SQLite | Database management |
| Pandas | Data handling |
| Plotly | Interactive visualizations |

## 6. System Workflow

1. Upload CCTV video.
2. Process video frames using OpenCV.
3. Detect objects using YOLO.
4. Track detected objects using ByteTrack.
5. Analyze movement and interactions.
6. Generate and store incident records.
7. Group incidents into investigation cases.
8. Analyze possible contextual relationships.
9. Display investigation findings and reports.

## 7. Current Implementation Status

The current prototype includes:
- CCTV video upload and processing.
- Object detection and tracking.
- Movement and interaction analysis.
- Incident management.
- Investigation case creation and incident linking.
- Rule-based contextual incident correlation.
- Investigation timelines and reports.

The current implementation uses uploaded video and rule-based analysis. Real-time multi-camera intelligence and advanced open-world reasoning are planned future enhancements.

## 8. Future Scope

- Real-time CCTV stream integration.
- Multi-camera event correlation.
- Advanced spatial and semantic reasoning.
- Improved anomaly detection.
- Natural-language investigation queries.
- Scalable deployment for campuses and public spaces.

## 9. Target Users

- Campus security teams.
- Public safety departments.
- Security control rooms.
- Investigation teams.

## 10. Team

**Project:** NEMESIS-X

**Team Name:** [ADD TEAM NAME]

**Team Members:** [ADD ALL TEAM MEMBERS]

---

NEMESIS-X aims to transform traditional CCTV footage into structured, explainable and actionable investigation insights.
