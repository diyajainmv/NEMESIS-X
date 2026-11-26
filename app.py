import html
import streamlit as st
import av
import os
import json
import hashlib
import pandas as pd
import plotly.express as px
from modules.case_intelligence import analyze_case

from datetime import datetime, timedelta

from modules.evidence_manager import save_evidence, get_evidence_path
from modules.integration_pipeline import run_video_analysis
from modules.incident_manager import (
    save_case_report,
    get_case_report,
    create_case,
    get_cases,
    get_case,
    update_case,
    link_incident_to_case,
    unlink_incident_from_case,
    get_case_incidents,
    add_case_note,
    get_case_notes,
    init_db,
    add_incident,
    get_incidents,
    update_status,

)


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="NEMESIS-X | Video Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================
# CUSTOM DESIGN
# ==========================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #08111f 0%, #101b2d 100%);
    color: #e8f0fa;
}
[data-testid="stSidebar"] {
    background: #0b1424;
    border-right: 1px solid #243650;
}
[data-testid="stSidebar"] h1 {
    color: #38d9f5;
    font-weight: 800;
}
h1, h2, h3 {
    color: #f0f6ff;
    font-weight: 700;
}
p, label {
    color: #b8c7da;
}
[data-testid="stMetric"] {
    background: #14243a;
    border: 1px solid #29425e;
    padding: 18px;
    border-radius: 14px;
}
[data-testid="stMetricValue"] {
    color: #38d9f5;
}
[data-testid="stMetricLabel"] {
    color: #a9bdd4;
}
.stButton > button {
    background: linear-gradient(90deg, #087eae, #6554c0);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    padding: 10px 18px;
    transition: 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #079acb, #8067e8);
    color: white;
    border: none;
    transform: translateY(-2px);
}
div[data-testid="stFileUploader"] {
    background: #14243a;
    border: 1px dashed #38bdf8;
    border-radius: 14px;
    padding: 14px;
}
div[data-testid="stExpander"] {
    background: #14243a;
    border: 1px solid #29425e;
    border-radius: 10px;
}
hr {
    border-color: #29425e;
}
[data-testid="stDataFrame"] {
    border: 1px solid #29425e;
    border-radius: 10px;
}
.small-caption {
    color: #8da7c4;
    font-size: 13px;
}
.hero {
    background: linear-gradient(120deg, #102c49, #25204d);
    padding: 28px;
    border: 1px solid #315375;
    border-radius: 18px;
    margin-bottom: 25px;
}
.hero-title {
    font-size: 34px;
    font-weight: 800;
    color: #ffffff;
}
.hero-subtitle {
    font-size: 15px;
    color: #b7cee5;
}
.status-online {
    color: #4ade80;
    font-weight: 700;
}
.event-card {
    background: rgba(20, 36, 58, 0.92);
    border: 1px solid #29425e;
    border-left: 5px solid var(--event-color);
    border-radius: 12px;
    padding: 15px 18px;
    margin: 10px 0;
}
.event-heading {
    color: #f0f6ff;
    font-size: 17px;
    font-weight: 700;
}
.event-meta {
    color: #a9bdd4;
    font-size: 13px;
}
.event-description {
    color: #d2deeb;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# SESSION STATE
# ==========================================

defaults = {
    "latest_evidence_path": None,
    "latest_video_hash": None,
    "latest_video_name": None,
    "saved_evidence": {},
    "latest_analysis_result": None,
    "videos_analysed": 0,
    "events_detected": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# DATABASE
# ==========================================

init_db()


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def section_title(title, subtitle=None):
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def priority_color(priority):
    colors = {
        "Critical": "🔴",
        "High": "🟠",
        "Medium": "🟡",
        "Low": "🟢",
    }
    return colors.get(priority, "⚪")


def parse_evidence_frames(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return []


def anomaly_level(score):
    """Convert a heuristic anomaly score into a display category."""
    if score >= 0.70:
        return "HIGH", "#ef4444"
    if score >= 0.40:
        return "MEDIUM", "#f59e0b"
    return "LOW", "#22c55e"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.markdown("# 🔍 NEMESIS-X")
    st.caption("AI VIDEO INTELLIGENCE PLATFORM")
    st.markdown("---")
    st.markdown("### NAVIGATION")

    page = st.radio(
        "Go to",
        [
            "🏠 Overview",
            "🎥 Video Analysis",
            "🚨 Incident Management",
            "🔎 Investigation",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### SYSTEM STATUS")
    st.markdown(
        '<p class="status-online">● SYSTEM READY</p>',
        unsafe_allow_html=True,
    )
    st.caption("YOLO · ByteTrack · Event Intelligence")
    st.markdown("---")
    st.caption("NEMESIS-X | AI Security Research")


# ==========================================
# HEADER
# ==========================================

st.markdown("""
<div class="hero">
    <div class="hero-title">NEMESIS-X</div>
    <div class="hero-subtitle">
        Proactive Video Intelligence & Autonomous Event Investigation
    </div>
    <br>
    <div style="color:#38d9f5;font-size:14px;font-weight:600;">
        DETECT  ·  TRACK  ·  UNDERSTAND  ·  INVESTIGATE
    </div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# OVERVIEW
# ==========================================

if page == "🏠 Overview":

    section_title(
        "Security Overview",
        "Your video intelligence activity at a glance.",
    )

    incidents = get_incidents()

    pending_count = sum(
        1 for item in incidents if item["status"] != "Resolved"
    )
    resolved_count = sum(
        1 for item in incidents if item["status"] == "Resolved"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎥 Videos Analysed", st.session_state["videos_analysed"])
    col2.metric("🧠 Events Detected", st.session_state["events_detected"])
    col3.metric("🚨 Pending Incidents", pending_count)
    col4.metric("✅ Resolved", resolved_count)

    st.markdown("---")
    left, right = st.columns([1.5, 1])

    with left:
        section_title("Recent Incidents", "Latest recorded events.")

        if incidents:
            for incident in incidents[:5]:
                with st.container(border=True):
                    st.markdown(
                        f"**#{incident['incident_id']} · "
                        f"{html.escape(str(incident['event_type']))}**"
                    )
                    st.caption(
                        f"{priority_color(incident['priority'])} "
                        f"{incident['priority']} Priority"
                        f"  |  {incident['status']}"
                    )
                    st.caption(
                        f"📍 {incident['camera_location'] or 'Unknown'}"
                        f"  |  {incident['timestamp']}"
                    )
        else:
            st.info("No incidents yet. Start by analysing a video.")

    with right:
        section_title("Platform Capabilities")
        capabilities = [
            ("🎯", "YOLO Detection", "Detect objects in video frames"),
            ("🔗", "ByteTrack", "Track objects across frames"),
            ("🧠", "Event Intelligence", "Analyse movement and interactions"),
            ("🚨", "Incident Management", "Review and manage events"),
        ]
        for icon, title, description in capabilities:
            with st.container(border=True):
                st.markdown(f"**{icon} {title}**")
                st.caption(description)

    st.markdown("---")
    section_title("Incident Priority Overview")

    priority_counts = {
        "Critical": sum(1 for i in incidents if i["priority"] == "Critical"),
        "High": sum(1 for i in incidents if i["priority"] == "High"),
        "Medium": sum(1 for i in incidents if i["priority"] == "Medium"),
        "Low": sum(1 for i in incidents if i["priority"] == "Low"),
    }

    if incidents:
        priority_df = pd.DataFrame(
            list(priority_counts.items()),
            columns=["Priority", "Count"],
        )
        fig = px.bar(
            priority_df,
            x="Priority",
            y="Count",
            color="Priority",
            color_discrete_map={
                "Critical": "#ef4444",
                "High": "#f97316",
                "Medium": "#eab308",
                "Low": "#22c55e",
            },
        )
        fig.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#dce8f5",
            showlegend=False,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.caption("Priority statistics will appear after incidents are generated.")


# ==========================================
# VIDEO ANALYSIS
# ==========================================

elif page == "🎥 Video Analysis":

    section_title(
        "Video Intelligence Workspace",
        "Upload CCTV footage and analyse objects, tracking and events.",
    )

    video = st.file_uploader(
        "UPLOAD CCTV FOOTAGE",
        type=["mp4", "avi", "mov"],
        help="Supported formats: MP4, AVI and MOV. Maximum 200 MB.",
        key="cctv_video_uploader",
    )

    saved_path = None
    file_hash = None
    file_name = None

    # --------------------------------------
    # HANDLE UPLOAD / RESTORE LAST VIDEO
    # --------------------------------------

    if video is not None:
        file_hash = hashlib.sha256(video.getbuffer()).hexdigest()
        file_name = video.name

        saved_evidence = st.session_state["saved_evidence"]
        saved_path = saved_evidence.get(file_hash)

        if saved_path is None:
            try:
                saved_path = save_evidence(video)
                saved_evidence[file_hash] = saved_path
                st.session_state["saved_evidence"] = saved_evidence
                st.success("Video evidence saved successfully.")
            except Exception as error:
                st.error(f"Unable to save video: {error}")
                saved_path = None

        if saved_path:
            st.session_state["latest_evidence_path"] = saved_path
            st.session_state["latest_video_hash"] = file_hash
            st.session_state["latest_video_name"] = file_name

    else:
        saved_path = st.session_state.get("latest_evidence_path")
        file_hash = st.session_state.get("latest_video_hash")
        file_name = st.session_state.get("latest_video_name")

    # --------------------------------------
    # DISPLAY VIDEO AND METADATA
    # --------------------------------------

    if saved_path:

        try:
            video_path = get_evidence_path(saved_path)

            if not video_path.exists():
                st.error("Saved video file could not be found.")
            else:
                with st.container(border=True):
                    st.markdown("### 🎬 Selected Video")
                    st.markdown(f"**{file_name or video_path.name}**")
                    st.video(str(video_path))

                section_title("Video Information")
                file_size = os.path.getsize(video_path) / (1024 * 1024)

                width = 0
                height = 0
                fps = 0.0
                total_frames = 0
                duration = 0.0

                with av.open(str(video_path)) as container:
                    video_stream = next(
                        (
                            stream for stream in container.streams
                            if stream.type == "video"
                        ),
                        None,
                    )

                    if video_stream is None:
                        st.error("No video stream found.")
                    else:
                        width = video_stream.codec_context.width or 0
                        height = video_stream.codec_context.height or 0
                        fps = float(video_stream.average_rate or 0)
                        total_frames = video_stream.frames or 0

                        if video_stream.duration is not None:
                            duration = float(
                                video_stream.duration * video_stream.time_base
                            )
                        elif container.duration is not None:
                            duration = container.duration / 1_000_000

                        if total_frames == 0 and fps > 0 and duration > 0:
                            total_frames = int(duration * fps)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric(
                    "Resolution",
                    f"{width} × {height}" if width and height else "N/A",
                )
                col2.metric("Frame Rate", f"{fps:.2f} FPS" if fps else "N/A")
                col3.metric(
                    "Total Frames",
                    f"{total_frames:,}" if total_frames else "N/A",
                )
                col4.metric("File Size", f"{file_size:.2f} MB")

                minutes = int(duration // 60)
                seconds = int(duration % 60)
                st.caption(f"Video Duration: {minutes} min {seconds} sec")

                # ----------------------------------
                # START AI ANALYSIS
                # ----------------------------------

                st.markdown("---")
                st.markdown("### ⚡ AI Video Analysis")
                st.caption(
                    "YOLO detects objects · ByteTrack tracks identities · "
                    "Event Intelligence analyses activity."
                )

                if st.button(
                    "🚀 START AI ANALYSIS",
                    type="primary",
                    width="stretch",
                ):
                    try:
                        progress_bar = st.progress(
                            0,
                            text="Preparing video analysis...",
                        )
                        analysis_started = datetime.now()
                        frame_placeholder = st.empty()

                        def update_progress(value, message):
                            progress_bar.progress(value, text=message)

                        def update_frame(frame, frame_number, timestamp):
                            frame_placeholder.image(
                                frame,
                                caption=(
                                    f"YOLO + ByteTrack | Frame {frame_number} | "
                                    f"{timestamp:.2f} seconds"
                                ),
                                width="stretch",
                            )

                        result = run_video_analysis(
                            str(video_path),
                            progress_callback=update_progress,
                            frame_callback=update_frame,
                        )

                        events = result.get("events", [])
                        created_count = 0

                        # ----------------------------------
                        # SAVE GENERATED INCIDENTS
                        # ----------------------------------

                        for event in events:
                            score = safe_float(event.get("anomaly_score", 0))

                            if score >= 0.70:
                                priority = "High"
                            elif score >= 0.40:
                                priority = "Medium"
                            else:
                                priority = "Low"

                            video_seconds = safe_float(event.get("timestamp", 0))
                            event_datetime = (
                                analysis_started
                                + timedelta(seconds=video_seconds)
                            )

                            incident_id = add_incident(
                                event_type=event.get("event_type", "Unknown Event"),
                                timestamp=event_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                                camera_location="Uploaded Video",
                                priority=priority,
                                evidence=str(saved_path),
                                event_id=event.get("event_id"),
                                run_id=result.get("run_id"),
                                anomaly_score=score,
                                explanation=event.get("explanation"),
                                evidence_frames=event.get("evidence_frames", []),
                                video_timestamp=video_seconds,
                            )

                            if incident_id is not None:
                                created_count += 1

                        # ----------------------------------
                        # SAVE RESULTS IN SESSION
                        # ----------------------------------

                        st.session_state["latest_analysis_result"] = {
                            "source_hash": file_hash,
                            "run_id": result.get("run_id"),
                            "events": events,
                            "frames_processed": result.get("frames_processed", 0),
                            "frames_annotated": result.get("frames_annotated", 0),
                            "created_count": created_count,
                            "annotated_dir": result.get("annotated_dir"),
                        }

                        st.session_state["videos_analysed"] += 1
                        st.session_state["events_detected"] += len(events)

                        progress_bar.progress(100, text="Analysis completed!")
                        st.success(
                            f"Analysis completed! {created_count} new incidents created."
                        )
                        st.rerun()

                    except Exception as error:
                        st.error(f"Analysis failed: {error}")

                # ----------------------------------
                # DISPLAY ANALYSIS RESULTS
                # ----------------------------------

                latest_result = st.session_state.get("latest_analysis_result")

                if (
                    latest_result
                    and latest_result.get("source_hash") == file_hash
                ):
                    st.markdown("---")
                    section_title(
                        "AI Analysis Results",
                        "Summary of the latest analysis run.",
                    )

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric(
                        "Frames Processed",
                        latest_result.get("frames_processed", 0),
                    )
                    col2.metric(
                        "Frames Annotated",
                        latest_result.get("frames_annotated", 0),
                    )
                    col3.metric(
                        "Events Detected",
                        len(latest_result.get("events", [])),
                    )
                    col4.metric(
                        "Incidents Created",
                        latest_result.get("created_count", 0),
                    )

                    # ----------------------------------
                    # ANNOTATED FRAME GALLERY
                    # ----------------------------------

                    annotated_dir = latest_result.get("annotated_dir")

                    if annotated_dir and os.path.isdir(annotated_dir):
                        with st.expander("🖼️ View Annotated Frames"):
                            frame_files = sorted(
                                [
                                    os.path.join(annotated_dir, name)
                                    for name in os.listdir(annotated_dir)
                                    if name.lower().endswith((".jpg", ".jpeg", ".png"))
                                ]
                            )

                            if frame_files:
                                selected_frames = frame_files[:min(6, len(frame_files))]
                                cols = st.columns(2)

                                for index, frame_file in enumerate(selected_frames):
                                    with cols[index % 2]:
                                        st.image(
                                            frame_file,
                                            caption=os.path.basename(frame_file),
                                            width="stretch",
                                        )
                            else:
                                st.caption("No annotated frame images were saved.")

                    # ----------------------------------
                    # COLOUR-CODED EVENT TIMELINE
                    # ----------------------------------

                    section_title(
                        "🚨 Event Intelligence Timeline",
                        "Events are grouped by heuristic anomaly score.",
                    )

                    events = latest_result.get("events", [])

                    if events:
                        severity_filter = st.selectbox(
                            "Filter events by severity",
                            ["All", "HIGH", "MEDIUM", "LOW"],
                            key="event_severity_filter",
                        )

                        displayed_count = 0

                        for event_index, event in enumerate(events):
                            score = safe_float(event.get("anomaly_score", 0))
                            level, color = anomaly_level(score)

                            if severity_filter != "All" and level != severity_filter:
                                continue

                            displayed_count += 1

                            event_type = html.escape(
                                str(event.get("event_type", "Unknown Event"))
                                .replace("_", " ")
                                .title()
                            )
                            explanation = html.escape(
                                str(event.get("explanation", "No explanation available."))
                            )
                            track_ids = html.escape(
                                str(event.get("track_ids", []))
                            )
                            timestamp = safe_float(event.get("timestamp", 0))
                            event_id = html.escape(
                                str(event.get("event_id", f"Event {event_index + 1}"))
                            )

                            st.markdown(
                                f"""
                                <div class="event-card" style="--event-color:{color};">
                                    <div style="display:flex;justify-content:space-between;
                                                align-items:center;gap:12px;flex-wrap:wrap;">
                                        <span class="event-heading">{event_type}</span>
                                        <span style="background:{color};color:#ffffff;
                                                     padding:5px 12px;border-radius:20px;
                                                     font-size:12px;font-weight:800;">
                                            {level}
                                        </span>
                                    </div>
                                    <div class="event-meta">
                                        {event_id} &nbsp;·&nbsp;
                                        Video time: {timestamp:.2f}s &nbsp;·&nbsp;
                                        Anomaly score: {score:.2f}
                                    </div>
                                    <div class="event-description">{explanation}</div>
                                    <div class="event-meta">Track IDs: {track_ids}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            with st.expander(f"Evidence details — {event_id}"):
                                st.write(
                                    "**Evidence frames:**",
                                    event.get("evidence_frames", []),
                                )
                                st.write(
                                    "**Video timestamp:**",
                                    f"{timestamp:.2f} seconds",
                                )
                                st.write("**Track IDs:**", event.get("track_ids", []))
                                st.write("**Event ID:**", event.get("event_id"))

                        if displayed_count == 0:
                            st.info("No events match the selected severity filter.")
                    else:
                        st.success("No events were generated for this video.")

                    st.caption(
                        "Anomaly scores are heuristic indicators, not confirmed "
                        "security threats. HIGH/MEDIUM/LOW are review priorities; "
                        "human verification is required."
                    )

        except Exception as error:
            st.error(f"Unable to display video: {error}")

    else:
        st.info("👆 Upload a CCTV video above to open the analysis workspace.")


# ==========================================
# INCIDENT MANAGEMENT
# ==========================================

elif page == "🚨 Incident Management":

    section_title(
        "Incident Management Center",
        "Create, monitor and manage generated security incidents.",
    )

    incidents = get_incidents()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Incidents", len(incidents))
    col2.metric(
        "Open Incidents",
        sum(1 for i in incidents if i["status"] != "Resolved"),
    )
    col3.metric(
        "High Priority",
        sum(1 for i in incidents if i["priority"] in ["High", "Critical"]),
    )

    st.markdown("---")

    # --------------------------------------
    # CREATE MANUAL INCIDENT
    # --------------------------------------

    with st.expander("➕ Create Manual Incident"):
        with st.form("incident_form"):
            event_type = st.selectbox(
                "Event Type",
                [
                    "Unusual Activity",
                    "Object Detection",
                    "Suspicious Movement",
                    "Other",
                ],
            )
            camera_location = st.text_input(
                "Camera Location",
                placeholder="Example: Camera 01",
            )
            priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High", "Critical"],
            )
            evidence = st.text_input(
                "Evidence File",
                value=st.session_state.get("latest_evidence_path") or "",
            )

            submitted = st.form_submit_button(
                "Create Incident",
                width="stretch",
            )

            if submitted:
                if not camera_location.strip():
                    st.error("Please enter a camera location.")
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    incident_id = add_incident(
                        event_type,
                        timestamp,
                        camera_location,
                        priority,
                        evidence.strip(),
                    )
                    if incident_id is not None:
                        st.success(f"Incident #{incident_id} created.")
                    else:
                        st.warning("Incident was not added. Check the database.")
                    st.rerun()

    st.markdown("---")
    section_title("Incident Records")
    incidents = get_incidents()

    if incidents:
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "New", "Under Review", "Escalated", "Resolved"],
            )

        with filter_col2:
            priority_filter = st.selectbox(
                "Filter by Priority",
                ["All", "Critical", "High", "Medium", "Low"],
            )

        filtered = incidents

        if status_filter != "All":
            filtered = [i for i in filtered if i["status"] == status_filter]

        if priority_filter != "All":
            filtered = [i for i in filtered if i["priority"] == priority_filter]

        display_rows = [
            {
                "ID": incident["incident_id"],
                "Event": incident["event_type"],
                "Location": incident["camera_location"],
                "Priority": incident["priority"],
                "Status": incident["status"],
                "Timestamp": incident["timestamp"],
            }
            for incident in filtered
        ]

        if display_rows:
            st.dataframe(
                pd.DataFrame(display_rows),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No incidents match these filters.")

        st.markdown("---")
        section_title("Update Incident Status")

        incident_ids = [item["incident_id"] for item in incidents]
        selected_id = st.selectbox(
            "Select Incident",
            incident_ids,
            format_func=lambda x: (
                f"Incident #{x} - "
                f"{next(i['event_type'] for i in incidents if i['incident_id'] == x)}"
            ),
        )

        selected = next(
            i for i in incidents if i["incident_id"] == selected_id
        )
        st.caption(f"Current status: {selected['status']}")

        new_status = st.selectbox(
            "Change Status",
            ["New", "Under Review", "Escalated", "Resolved"],
            index=(
                ["New", "Under Review", "Escalated", "Resolved"].index(
                    selected["status"]
                )
                if selected["status"] in ["New", "Under Review", "Escalated", "Resolved"]
                else 0
            ),
        )

        if st.button("💾 Update Status", type="primary"):
            if update_status(selected_id, new_status):
                st.success("Incident status updated.")
                st.rerun()
            else:
                st.error("Unable to update incident.")
    else:
        st.info("No incidents found. Analyse a video or create an incident.")


# ==========================================
# INVESTIGATION
# ==========================================

elif page == "🔎 Investigation":

    section_title(
        "Investigation Center",
        "Connect incidents, manage cases, review AI findings and examine evidence.",
    )

    incidents = get_incidents()
    cases = get_cases()

    # ==========================================
    # INVESTIGATION OVERVIEW
    # ==========================================

    high_priority = sum(
        1 for i in incidents
        if i.get("priority") in ["High", "Critical"]
    )
    resolved = sum(
        1 for i in incidents if i.get("status") == "Resolved"
    )
    open_cases = sum(
        1 for c in cases if c.get("status") != "Closed"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Incidents", len(incidents))
    col2.metric("High Priority", high_priority)
    col3.metric("Investigation Cases", len(cases))
    col4.metric("Active Cases", open_cases)

    st.markdown("---")

    # ==========================================
    # INVESTIGATION CASE FILES
    # ==========================================

    section_title(
        "Investigation Case Files",
        "Group related incidents into a single investigation.",
    )

    with st.expander("Create New Investigation Case", expanded=False):

        with st.form("create_investigation_case_form"):

            case_title = st.text_input(
                "Case Title",
                placeholder="Example: Suspicious Activity - Main Entrance",
            )

            case_description = st.text_area(
                "Case Description",
                placeholder="Describe what needs to be investigated...",
            )

            investigator = st.text_input(
                "Assigned Investigator",
                placeholder="Investigator name",
            )

            case_priority = st.selectbox(
                "Case Priority",
                ["Low", "Medium", "High", "Critical"],
                index=1,
            )

            create_button = st.form_submit_button(
                "Create Investigation Case",
                use_container_width=True,
            )

            if create_button:

                if not case_title.strip():
                    st.error("Please enter a case title.")

                else:
                    new_case_id = create_case(
                        case_title,
                        case_description,
                        investigator,
                        case_priority,
                    )

                    st.success(
                        f"Investigation Case #{new_case_id} created."
                    )
                    st.rerun()

    cases = get_cases()

    if cases:

        st.markdown("### Existing Investigation Cases")

        case_table = pd.DataFrame(cases)

        st.dataframe(
            case_table[
                [
                    "case_id",
                    "title",
                    "investigator",
                    "priority",
                    "status",
                    "incident_count",
                    "updated_at",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        selected_case_id = st.selectbox(
            "Select Investigation Case",
            [c["case_id"] for c in cases],
            format_func=lambda x: (
                f"Case #{x} - "
                + next(
                    c["title"] for c in cases
                    if c["case_id"] == x
                )
            ),
            key="selected_investigation_case",
        )

        selected_case = get_case(selected_case_id)

        if selected_case:

            st.markdown("---")
            st.markdown(
                f"### Case #{selected_case['case_id']}: "
                f"{selected_case['title']}"
            )

            # ==========================================
            # AI CASE INVESTIGATION
            # ==========================================

            st.markdown("---")

            section_title(
                "AI Case Investigation",
                "Discover possible relationships between linked incidents.",
            )

            col1, col2 = st.columns([1, 3])

            with col1:
                run_case_analysis = st.button(
                    "Analyze Case",
                    type="primary",
                    use_container_width=True,
                    key=f"analyze_case_{selected_case_id}",
                )

            with col2:
                st.caption(
                    "Analyzes linked incident metadata and creates "
                    "a persistent investigation report."
                )

            if run_case_analysis:

                case_incidents = get_case_incidents(
                    selected_case_id
                )

                with st.spinner("Analyzing connected incidents..."):

                    report = analyze_case(case_incidents)

                    save_case_report(
                        selected_case_id,
                        report,
                    )

                st.success("Investigation analysis completed.")
                st.rerun()

            report = get_case_report(selected_case_id)

            if report:

                st.markdown("### Investigation Report")

                st.caption(
                    f"Analysis type: {report.get('analysis_type', 'Unknown')}"
                )

                st.info(report.get("summary", "No summary available."))

                report_col1, report_col2 = st.columns(2)

                report_col1.metric(
                    "Incidents Analyzed",
                    report.get("incident_count", 0),
                )

                report_col2.metric(
                    "Possible Connections",
                    len(report.get("connections", [])),
                )

                # Timeline
                st.markdown("#### Combined Event Timeline")

                for event in report.get("timeline", []):

                    with st.container(border=True):

                        st.write(
                            f"**Incident #{event['incident_id']} — "
                            f"{event['event_type']}**"
                        )

                        st.caption(
                            f"{event['timestamp']} | "
                            f"Location: {event['location']}"
                        )

                        if event.get("explanation"):
                            st.write(event["explanation"])

                # Possible relationships
                st.markdown("#### Possible Incident Connections")

                connections = report.get("connections", [])

                if connections:

                    for connection in connections:

                        with st.container(border=True):

                            st.write(
                                f"**Incident #{connection['incident_a']} "
                                f"↔ Incident #{connection['incident_b']}**"
                            )

                            st.write(
                                f"Relationship: {connection['strength']}"
                            )

                            st.progress(
                                connection["score"],
                                text=(
                                    f"Contextual match score: "
                                    f"{connection['score']:.0%}"
                                ),
                            )

                            for reason in connection["reasons"]:
                                st.write(f"• {reason}")

                            st.warning(connection["warning"])

                else:
                    st.info(
                        "No possible relationships were identified "
                        "from the available metadata."
                    )

                # High anomaly events
                st.markdown("#### High Anomaly Incidents")

                anomalies = report.get("high_anomalies", [])

                if anomalies:

                    for anomaly in anomalies:

                        st.write(
                            f"Incident #{anomaly['incident_id']} — "
                            f"{anomaly['event_type']} — "
                            f"Score: {anomaly['score']:.0%}"
                        )

                else:
                    st.info("No incidents crossed the high anomaly threshold.")

                # Warnings
                st.markdown("#### Investigation Warnings")

                for warning in report.get("warnings", []):
                    st.warning(warning)

                # Recommendations
                st.markdown("#### Recommended Investigator Actions")

                for recommendation in report.get("recommendations", []):
                    st.write(f"• {recommendation}")

                st.caption(
                    f"Report generated: {report.get('generated_at', 'Unknown')}"
                )

            else:

                st.info(
                    "No investigation report exists yet. "
                    "Link incidents and click Analyze Case."
                )


            # ----------------------------------
            # UPDATE CASE DETAILS
            # ----------------------------------

            with st.expander("Edit Case Details"):

                with st.form("update_case_form"):

                    edit_title = st.text_input(
                        "Case Title",
                        value=selected_case["title"],
                    )

                    edit_description = st.text_area(
                        "Description",
                        value=selected_case.get("description") or "",
                    )

                    edit_investigator = st.text_input(
                        "Investigator",
                        value=selected_case.get("investigator") or "",
                    )

                    priorities = [
                        "Low", "Medium", "High", "Critical"
                    ]

                    edit_priority = st.selectbox(
                        "Priority",
                        priorities,
                        index=(
                            priorities.index(selected_case["priority"])
                            if selected_case["priority"] in priorities
                            else 1
                        ),
                    )

                    statuses = [
                        "Open",
                        "Under Investigation",
                        "Closed",
                    ]

                    edit_status = st.selectbox(
                        "Case Status",
                        statuses,
                        index=(
                            statuses.index(selected_case["status"])
                            if selected_case["status"] in statuses
                            else 0
                        ),
                    )

                    update_button = st.form_submit_button(
                        "Save Case Changes",
                        use_container_width=True,
                    )

                    if update_button:

                        if not edit_title.strip():
                            st.error("Case title cannot be empty.")

                        else:
                            update_case(
                                selected_case_id,
                                edit_title,
                                edit_description,
                                edit_investigator,
                                edit_priority,
                                edit_status,
                            )

                            st.success("Case updated successfully.")
                            st.rerun()

            # ----------------------------------
            # LINK INCIDENTS
            # ----------------------------------

            st.markdown("### Link Incidents to This Case")

            linked_incidents = get_case_incidents(
                selected_case_id
            )

            linked_ids = {
                i["incident_id"] for i in linked_incidents
            }

            available_incidents = [
                i for i in incidents
                if i["incident_id"] not in linked_ids
            ]

            if available_incidents:

                incident_to_link = st.selectbox(
                    "Choose an incident to link",
                    [i["incident_id"] for i in available_incidents],
                    format_func=lambda x: (
                        f"Incident #{x} - "
                        + next(
                            i["event_type"] for i in available_incidents
                            if i["incident_id"] == x
                        )
                    ),
                    key=f"link_incident_{selected_case_id}",
                )

                if st.button(
                    "Link Incident to Case",
                    key=f"link_button_{selected_case_id}",
                ):

                    success = link_incident_to_case(
                        selected_case_id,
                        incident_to_link,
                    )

                    if success:
                        st.success("Incident linked successfully.")
                    else:
                        st.info("Incident was already linked.")

                    st.rerun()

            else:
                st.info(
                    "No additional incidents available to link."
                )

            # ----------------------------------
            # LINKED INCIDENT RECORDS
            # ----------------------------------

            st.markdown("### Linked Incident Records")

            linked_incidents = get_case_incidents(
                selected_case_id
            )

            if linked_incidents:

                for linked in linked_incidents:

                    with st.container(border=True):

                        col1, col2 = st.columns([4, 1])

                        with col1:
                            st.markdown(
                                f"**Incident #{linked['incident_id']} "
                                f"- {linked['event_type']}**"
                            )

                            st.write(
                                f"Priority: {linked['priority']} | "
                                f"Status: {linked['status']}"
                            )

                            st.caption(
                                f"Timestamp: {linked['timestamp']}"
                            )

                        with col2:

                            if st.button(
                                "Unlink",
                                key=(
                                    f"unlink_{selected_case_id}_"
                                    f"{linked['incident_id']}"
                                ),
                            ):

                                unlink_incident_from_case(
                                    selected_case_id,
                                    linked["incident_id"],
                                )

                                st.rerun()

            else:
                st.info(
                    "No incidents linked to this case yet."
                )

            # ----------------------------------
            # INVESTIGATOR NOTES
            # ----------------------------------

            st.markdown("### Investigator Notes")

            with st.form(
                f"case_note_form_{selected_case_id}"
            ):

                note_author = st.text_input(
                    "Investigator Name",
                    value=selected_case.get("investigator") or "",
                )

                note_text = st.text_area(
                    "Add Investigation Note",
                    placeholder=(
                        "Record observations, findings, "
                        "suspected connections or actions taken..."
                    ),
                )

                save_note = st.form_submit_button(
                    "Save Investigation Note",
                    use_container_width=True,
                )

                if save_note:

                    if not note_text.strip():
                        st.error("Please enter a note.")

                    else:
                        add_case_note(
                            selected_case_id,
                            note_text,
                            note_author,
                        )

                        st.success("Investigation note saved.")
                        st.rerun()

            notes = get_case_notes(selected_case_id)

            if notes:

                for note in notes:

                    with st.container(border=True):

                        st.write(note["note"])

                        st.caption(
                            f"By: {note['investigator'] or 'Unknown'} "
                            f"| {note['created_at']}"
                        )

            else:
                st.info("No investigation notes added yet.")

    else:
        st.info(
            "No investigation cases created yet. "
            "Create your first case above."
        )

    st.markdown("---")

    # ==========================================
    # INCIDENT TIMELINE
    # ==========================================

    section_title("Event Timeline")

    if incidents:

        df = pd.DataFrame(incidents)
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )
        valid_df = df.dropna(subset=["timestamp"]).copy()

        if not valid_df.empty:

            valid_df["incident_label"] = (
                "Incident #"
                + valid_df["incident_id"].astype(str)
                + " - "
                + valid_df["event_type"].astype(str)
            )

            fig = px.scatter(
                valid_df,
                x="timestamp",
                y="incident_label",
                color="priority",
                symbol="status",
                hover_data=[
                    "incident_id",
                    "event_type",
                    "camera_location",
                    "status",
                ],
                color_discrete_map={
                    "Critical": "#ef4444",
                    "High": "#f97316",
                    "Medium": "#eab308",
                    "Low": "#22c55e",
                },
            )

            fig.update_layout(
                height=450,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#dce8f5",
                xaxis_title="Date and Time",
                yaxis_title="Incident",
                legend_title="Priority",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        else:
            st.warning("No valid timestamps available.")

    else:
        st.info("No incidents available for the timeline.")

    st.markdown("---")

    # ==========================================
    # INDIVIDUAL INCIDENT INVESTIGATION
    # ==========================================

    section_title("Investigate an Incident")

    if incidents:

        selected_id = st.selectbox(
            "Choose Incident",
            [i["incident_id"] for i in incidents],
            format_func=lambda x: (
                f"Incident #{x} - "
                + next(
                    i["event_type"] for i in incidents
                    if i["incident_id"] == x
                )
            ),
        )

        incident = next(
            i for i in incidents
            if i["incident_id"] == selected_id
        )

        with st.container(border=True):

            st.markdown(f"### {incident['event_type']}")

            col1, col2 = st.columns(2)

            col1.write(
                f"**Incident ID:** #{incident['incident_id']}"
            )

            col2.write(
                f"**Priority:** {incident['priority']}"
            )

            col1.write(
                f"**Timestamp:** {incident['timestamp']}"
            )

            col2.write(
                f"**Location:** "
                f"{incident.get('camera_location') or 'Unknown'}"
            )

            st.write(
                f"**Status:** {incident['status']}"
            )

            if incident.get("anomaly_score") is not None:

                st.write(
                    f"**Anomaly Score:** "
                    f"{safe_float(incident['anomaly_score']):.3f}"
                )

            if incident.get("explanation"):

                st.markdown("#### AI Explanation")
                st.write(incident["explanation"])

            evidence_frames = parse_evidence_frames(
                incident.get("evidence_frames")
            )

            if evidence_frames:

                st.markdown("#### Evidence Frames")
                st.write(evidence_frames)

        # ----------------------------------
        # VIDEO EVIDENCE
        # ----------------------------------

        evidence_reference = incident.get("evidence")

        if evidence_reference:

            try:

                evidence_path = get_evidence_path(
                    evidence_reference
                )

                if evidence_path.exists():

                    section_title(
                        "Supporting Video Evidence"
                    )

                    st.video(str(evidence_path))

                    if incident.get("video_timestamp") is not None:

                        st.caption(
                            "Relevant video timestamp: "
                            f"{safe_float(incident['video_timestamp']):.2f} seconds"
                        )

                else:
                    st.warning(
                        "Referenced evidence file not found."
                    )

            except (ValueError, TypeError, OSError):

                st.warning("Invalid evidence reference.")

        else:

            st.info(
                "No video evidence linked to this incident."
            )

    else:

        st.info(
            "Upload and analyse CCTV footage to create incidents "
            "and begin investigations."
        )
