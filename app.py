
import streamlit as st

st.set_page_config(
    page_title="NEMESIS-X",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 NEMESIS-X")
st.caption(
    "Proactive Video Intelligence & Autonomous Event Investigation"
)

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

if page == "Overview":

    st.header("Security Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Videos Analysed", 0)
    col2.metric("Events Detected", 0)
    col3.metric("Pending Incidents", 0)
    col4.metric("Resolved Incidents", 0)

    st.subheader("Recent Activity")

    st.info(
        "No incidents available. Upload a video "
        "to begin analysis."
    )

elif page == "Video Analysis":

    st.header("CCTV Video Analysis")

    video = st.file_uploader(
        "Upload CCTV Footage",
        type=["mp4", "avi", "mov"]
    )

    if video:
        st.video(video)

        st.success("Video uploaded successfully!")

        if st.button("Start Analysis"):
            st.info(
                "Video processing module will be "
                "connected here."
            )

elif page == "Incident Management":

    st.header("Incident Management")

    st.info("Incident records will appear here.")

elif page == "Investigation":

    st.header("Event Investigation")

    st.info(
        "Event timeline and supporting evidence "
        "will appear here."
    )
