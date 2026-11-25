
import streamlit as st
import av
import tempfile
import os
import hashlib
import pandas as pd
import plotly.express as px

from datetime import datetime

from modules.incident_manager import (
    init_db,
    add_incident,
    get_incidents,
    update_status
)

from modules.evidence_manager import save_evidence


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="NEMESIS-X",
    page_icon="🔍",
    layout="wide"
)


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

init_db()


# ==========================================
# HEADER
# ==========================================

st.title("🔍 NEMESIS-X")

st.caption(
    "Proactive Video Intelligence & Autonomous Event Investigation"
)


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("NEMESIS-X")

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Video Analysis",
        "Incident Management",
        "Investigation"
    ]
)


# ==========================================
# OVERVIEW PAGE
# ==========================================

if page == "Overview":

    st.header("Security Overview")

    incidents = get_incidents()

    pending_count = sum(
        1 for item in incidents
        if item["status"] != "Resolved"
    )

    resolved_count = sum(
        1 for item in incidents
        if item["status"] == "Resolved"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Videos Analysed",
        0
    )

    col2.metric(
        "Events Detected",
        0
    )

    col3.metric(
        "Pending Incidents",
        pending_count
    )

    col4.metric(
        "Resolved Incidents",
        resolved_count
    )

    st.divider()

    st.subheader("Recent Activity")

    if incidents:

        for incident in incidents[:5]:

            st.write(
                f"**Incident #{incident['incident_id']}** "
                f"- {incident['event_type']}"
            )

            st.caption(
                f"Location: {incident['camera_location']} | "
                f"Priority: {incident['priority']} | "
                f"Status: {incident['status']}"
            )

    else:

        st.info(
            "No incidents available. Upload a video "
            "to begin analysis."
        )


# ==========================================
# VIDEO ANALYSIS PAGE
# ==========================================

elif page == "Video Analysis":

    st.header("CCTV Video Analysis")

    st.write(
        "Upload CCTV footage for analysis."
    )

    video = st.file_uploader(
        "Upload CCTV Footage",
        type=["mp4", "avi", "mov"],
        help="Upload an MP4, AVI or MOV video."
    )

    if video is not None:

        # --------------------------------------
        # PERMANENT EVIDENCE STORAGE
        # --------------------------------------

        file_hash = hashlib.sha256(
            video.getbuffer()
        ).hexdigest()

        saved_evidence = st.session_state.get(
            "saved_evidence", {}
        )

        saved_path = saved_evidence.get(file_hash)

        if saved_path is None:

            try:

                saved_path = save_evidence(video)

                saved_evidence[file_hash] = saved_path

                st.session_state["saved_evidence"] = saved_evidence

                st.session_state["latest_evidence_path"] = saved_path

                st.success(
                    "Video evidence saved permanently!"
                )

            except Exception as e:

                st.error(
                    f"Evidence storage error: {e}"
                )

                saved_path = None

        else:

            st.session_state["latest_evidence_path"] = saved_path

            st.success(
                "Video evidence is already saved!"
            )

        if saved_path:

            st.caption(
                f"Evidence location: {saved_path}"
            )

        # --------------------------------------
        # VIDEO PREVIEW
        # --------------------------------------

        st.subheader("Video Preview")

        st.video(video)

        st.success(
            "Video uploaded successfully!"
        )

        # --------------------------------------
        # VIDEO INFORMATION
        # --------------------------------------

        st.subheader("Video Information")

        file_name = video.name

        file_size = video.size / (1024 * 1024)

        col1, col2 = st.columns(2)

        col1.write(
            f"**Filename:** {file_name}"
        )

        col2.write(
            f"**File Size:** {file_size:.2f} MB"
        )

        # --------------------------------------
        # TEMPORARY VIDEO FILE
        # --------------------------------------

        temp_path = None

        try:

            suffix = os.path.splitext(video.name)[1]

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            ) as temp_file:

                temp_file.write(
                    video.getvalue()
                )

                temp_path = temp_file.name

            # ----------------------------------
            # PYAV VIDEO PROCESSING
            # ----------------------------------

            with av.open(temp_path) as container:

                video_stream = next(
                    (
                        stream
                        for stream in container.streams
                        if stream.type == "video"
                    ),
                    None
                )

                if video_stream is None:

                    st.error(
                        "No video stream found."
                    )

                else:

                    width = (
                        video_stream.codec_context.width
                    )

                    height = (
                        video_stream.codec_context.height
                    )

                    fps = float(
                        video_stream.average_rate or 0
                    )

                    total_frames = video_stream.frames

                    # Calculate duration

                    if video_stream.duration is not None:

                        duration = float(
                            video_stream.duration
                            * video_stream.time_base
                        )

                    elif container.duration is not None:

                        duration = (
                            container.duration / 1_000_000
                        )

                    else:

                        duration = 0

                    # Estimate frame count

                    if (
                        total_frames == 0
                        and fps > 0
                        and duration > 0
                    ):

                        total_frames = int(
                            duration * fps
                        )

                    # ----------------------------------
                    # DISPLAY METADATA
                    # ----------------------------------

                    st.divider()

                    st.subheader(
                        "Video Metadata"
                    )

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Resolution",
                        f"{width} × {height}"
                    )

                    col2.metric(
                        "Frame Rate",
                        f"{fps:.2f} FPS"
                        if fps > 0
                        else "Unavailable"
                    )

                    col3.metric(
                        "Total Frames",
                        f"{total_frames:,}"
                        if total_frames
                        else "Unavailable"
                    )

                    minutes = int(
                        duration // 60
                    )

                    seconds = int(
                        duration % 60
                    )

                    st.metric(
                        "Video Duration",
                        f"{minutes} min {seconds} sec"
                        if duration > 0
                        else "Unavailable"
                    )

                    # ----------------------------------
                    # START ANALYSIS
                    # ----------------------------------

                    st.divider()

                    st.subheader(
                        "Video Analysis"
                    )

                    if st.button(
                        "🚀 Start Analysis",
                        type="primary",
                        use_container_width=True
                    ):

                        st.success(
                            "Video metadata extracted successfully!"
                        )

                        st.warning(
                            "AI event detection is not integrated yet. "
                            "The detection module will be added "
                            "during the integration phase."
                        )

        except Exception as e:

            st.error(
                f"Video processing error: {e}"
            )

        finally:

            if (
                temp_path is not None
                and os.path.exists(temp_path)
            ):

                os.remove(temp_path)


# ==========================================
# INCIDENT MANAGEMENT PAGE
# ==========================================

elif page == "Incident Management":

    st.header("Incident Management")

    st.write(
        "Create, view and manage security incident records."
    )

    # --------------------------------------
    # CREATE INCIDENT
    # --------------------------------------

    st.subheader("Create New Incident")

    with st.form("incident_form"):

        event_type = st.selectbox(
            "Event Type",
            [
                "Unusual Activity",
                "Object Detection",
                "Suspicious Movement",
                "Other"
            ]
        )

        camera_location = st.text_input(
            "Camera Location",
            placeholder="Example: Camera 01"
        )

        priority = st.selectbox(
            "Priority",
            [
                "Low",
                "Medium",
                "High",
                "Critical"
            ]
        )

        evidence = st.text_input(
            "Evidence File",
            value=st.session_state.get(
                "latest_evidence_path", ""
            ),
            placeholder="Upload a video first"
        )

        submitted = st.form_submit_button(
            "Create Incident",
            use_container_width=True
        )

        if submitted:

            if not camera_location.strip():

                st.error(
                    "Please enter camera location."
                )

            else:

                timestamp = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                incident_id = add_incident(
                    event_type,
                    timestamp,
                    camera_location,
                    priority,
                    evidence.strip()
                )

                st.success(
                    f"Incident #{incident_id} created successfully!"
                )

                st.rerun()

    st.divider()

    # --------------------------------------
    # DISPLAY INCIDENT RECORDS
    # --------------------------------------

    st.subheader("Incident Records")

    incidents = get_incidents()

    if incidents:

        st.dataframe(
            incidents,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # ----------------------------------
        # UPDATE INCIDENT STATUS
        # ----------------------------------

        st.subheader(
            "Update Incident Status"
        )

        incident_ids = [
            item["incident_id"]
            for item in incidents
        ]

        selected_id = st.selectbox(
            "Select Incident ID",
            incident_ids
        )

        new_status = st.selectbox(
            "New Status",
            [
                "New",
                "Under Review",
                "Escalated",
                "Resolved"
            ]
        )

        if st.button(
            "Update Status",
            type="primary"
        ):

            updated = update_status(
                selected_id,
                new_status
            )

            if updated:

                st.success(
                    "Incident status updated successfully!"
                )

                st.rerun()

            else:

                st.error(
                    "Unable to update incident."
                )

    else:

        st.info(
            "No incident records available. "
            "Create your first incident above."
        )


# ==========================================
# INVESTIGATION PAGE
# ==========================================

elif page == "Investigation":

    st.header("Event Investigation")

    st.write(
        "Review incident timelines and supporting evidence."
    )

    incidents = get_incidents()

    if incidents:

        # ----------------------------------
        # CONVERT TO DATAFRAME
        # ----------------------------------

        df = pd.DataFrame(incidents)

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        valid_df = df.dropna(
            subset=["timestamp"]
        ).copy()

        # ----------------------------------
        # INCIDENT SUMMARY
        # ----------------------------------

        st.subheader(
            "Incident Summary"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Incidents",
            len(incidents)
        )

        high_priority = sum(
            1 for item in incidents
            if item["priority"] in ["High", "Critical"]
        )

        col2.metric(
            "High Priority",
            high_priority
        )

        resolved = sum(
            1 for item in incidents
            if item["status"] == "Resolved"
        )

        col3.metric(
            "Resolved",
            resolved
        )

        st.divider()

        # ----------------------------------
        # EVENT TIMELINE
        # ----------------------------------

        st.subheader(
            "Event Timeline"
        )

        if not valid_df.empty:

            valid_df["incident_label"] = (
                "Incident #"
                + valid_df["incident_id"].astype(str)
                + " - "
                + valid_df["event_type"]
            )

            fig = px.scatter(
                valid_df,
                x="timestamp",
                y="incident_label",
                color="status",
                hover_data=[
                    "incident_id",
                    "event_type",
                    "camera_location",
                    "priority",
                    "evidence"
                ],
                title="Chronological Incident Timeline",
                labels={
                    "timestamp": "Date and Time",
                    "incident_label": "Incident",
                    "status": "Current Status"
                }
            )

            fig.update_layout(
                height=450,
                xaxis_title="Date and Time",
                yaxis_title="Incident",
                legend_title="Incident Status"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.warning(
                "No valid incident timestamps available."
            )

        st.divider()

        # ----------------------------------
        # INVESTIGATION RECORDS
        # ----------------------------------

        st.subheader(
            "Investigation Records"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------
        # SELECT INCIDENT DETAILS
        # ----------------------------------

        st.divider()

        st.subheader(
            "Incident Details"
        )

        selected_id = st.selectbox(
            "Select Incident for Investigation",
            [
                item["incident_id"]
                for item in incidents
            ]
        )

        selected_incident = next(
            item for item in incidents
            if item["incident_id"] == selected_id
        )

        col1, col2 = st.columns(2)

        col1.write(
            f"**Event Type:** "
            f"{selected_incident['event_type']}"
        )

        col2.write(
            f"**Priority:** "
            f"{selected_incident['priority']}"
        )

        col1.write(
            f"**Timestamp:** "
            f"{selected_incident['timestamp']}"
        )

        col2.write(
            f"**Camera Location:** "
            f"{selected_incident['camera_location']}"
        )

        st.write(
            f"**Status:** {selected_incident['status']}"
        )

        st.write(
            f"**Evidence Reference:** "
            f"{selected_incident['evidence'] or 'Not provided'}"
        )

        # ----------------------------------
        # EVIDENCE PLAYBACK
        # ----------------------------------

        evidence_reference = selected_incident["evidence"]

        if evidence_reference:

            from modules.evidence_manager import get_evidence_path

            try:

                evidence_path = get_evidence_path(
                    evidence_reference
                )

                if evidence_path:

                    st.subheader("Supporting Video Evidence")

                    st.video(str(evidence_path))

                else:

                    st.warning(
                        "The referenced evidence file could not be found."
                    )

            except ValueError:

                st.warning(
                    "This incident does not contain a valid uploaded evidence path."
                )

        else:

            st.info(
                "No video evidence is linked to this incident."
            )

        st.info(
            "Automated event detection is not integrated yet. "
            "Incident timelines and evidence playback are available "
            "for records containing valid saved video paths."
        )

    else:

        st.info(
            "No incidents available for investigation. "
            "Create an incident in Incident Management first."
        )
