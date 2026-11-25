
import sqlite3
from pathlib import Path

# Database location
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "incidents.db"


# Initialize database
def init_db():

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            camera_location TEXT,
            priority TEXT,
            evidence TEXT,
            status TEXT DEFAULT 'New'
        )
    """)

    conn.commit()
    conn.close()


# Add a new incident
def add_incident(
    event_type,
    timestamp,
    camera_location,
    priority,
    evidence
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO incidents
        (event_type, timestamp, camera_location,
         priority, evidence, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        event_type,
        timestamp,
        camera_location,
        priority,
        evidence,
        "New"
    ))

    incident_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return incident_id


# Retrieve all incidents
def get_incidents():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM incidents
        ORDER BY incident_id DESC
    """)

    incidents = [
        dict(row) for row in cursor.fetchall()
    ]

    conn.close()

    return incidents


# Update incident status
def update_status(incident_id, new_status):

    allowed_statuses = [
        "New",
        "Under Review",
        "Escalated",
        "Resolved"
    ]

    if new_status not in allowed_statuses:
        raise ValueError("Invalid incident status")

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE incidents
        SET status = ?
        WHERE incident_id = ?
    """, (new_status, incident_id))

    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return updated
