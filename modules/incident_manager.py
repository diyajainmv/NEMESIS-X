
import sqlite3
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "incidents.db"

INCIDENT_STATUSES = ["New", "Under Review", "Escalated", "Resolved"]
CASE_STATUSES = ["Open", "Under Investigation", "Closed"]


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
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

        columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(incidents)"
            ).fetchall()
        }

        new_columns = {
            "event_id": "TEXT",
            "run_id": "TEXT",
            "anomaly_score": "REAL",
            "explanation": "TEXT",
            "evidence_frames": "TEXT",
            "video_timestamp": "REAL"
        }

        for column, data_type in new_columns.items():
            if column not in columns:
                conn.execute(
                    f"ALTER TABLE incidents ADD COLUMN {column} {data_type}"
                )

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS unique_analysis_event
            ON incidents(run_id, event_id)
        """)

        # Investigation case files
        conn.execute("""
            CREATE TABLE IF NOT EXISTS investigation_cases (
                case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                investigator TEXT,
                status TEXT DEFAULT 'Open',
                priority TEXT DEFAULT 'Medium',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Connect multiple incidents to one case
        conn.execute("""
            CREATE TABLE IF NOT EXISTS case_incidents (
                case_id INTEGER NOT NULL,
                incident_id INTEGER NOT NULL,
                linked_at TEXT NOT NULL,
                PRIMARY KEY (case_id, incident_id),
                FOREIGN KEY (case_id)
                    REFERENCES investigation_cases(case_id),
                FOREIGN KEY (incident_id)
                    REFERENCES incidents(incident_id)
            )
        """)

        # Investigator notes and case activity
        conn.execute("""
            CREATE TABLE IF NOT EXISTS case_notes (
                note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                investigator TEXT,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (case_id)
                    REFERENCES investigation_cases(case_id)
            )
        """)


def add_incident(
    event_type, timestamp, camera_location, priority, evidence,
    event_id=None, run_id=None, anomaly_score=None, explanation=None,
    evidence_frames=None, video_timestamp=None
):
    frames_json = (
        json.dumps(evidence_frames)
        if evidence_frames is not None else None
    )

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO incidents (
                event_type, timestamp, camera_location,
                priority, evidence, status, event_id,
                run_id, anomaly_score, explanation,
                evidence_frames, video_timestamp
            )
            VALUES (?, ?, ?, ?, ?, 'New', ?, ?, ?, ?, ?, ?)
        """, (
            event_type, timestamp, camera_location,
            priority, evidence, event_id, run_id,
            anomaly_score, explanation, frames_json,
            video_timestamp
        ))

        return cursor.lastrowid if cursor.rowcount else None


def get_incidents():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM incidents
            ORDER BY incident_id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def update_status(incident_id, new_status):
    if new_status not in INCIDENT_STATUSES:
        raise ValueError("Invalid incident status")

    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE incidents
            SET status = ?
            WHERE incident_id = ?
        """, (new_status, incident_id))

        return cursor.rowcount > 0


# ==========================================
# INVESTIGATION CASE MANAGEMENT
# ==========================================

def create_case(title, description="", investigator="", priority="Medium"):
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO investigation_cases (
                title, description, investigator,
                status, priority, created_at, updated_at
            )
            VALUES (?, ?, ?, 'Open', ?, ?, ?)
        """, (
            title.strip(),
            description.strip(),
            investigator.strip(),
            priority,
            now,
            now
        ))

        return cursor.lastrowid


def get_cases():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                c.*,
                COUNT(ci.incident_id) AS incident_count
            FROM investigation_cases c
            LEFT JOIN case_incidents ci
                ON c.case_id = ci.case_id
            GROUP BY c.case_id
            ORDER BY c.updated_at DESC
        """).fetchall()

        return [dict(row) for row in rows]


def get_case(case_id):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM investigation_cases
            WHERE case_id = ?
        """, (case_id,)).fetchone()

        return dict(row) if row else None


def update_case(case_id, title, description, investigator, priority, status):
    if status not in CASE_STATUSES:
        raise ValueError("Invalid case status")

    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE investigation_cases
            SET title = ?,
                description = ?,
                investigator = ?,
                priority = ?,
                status = ?,
                updated_at = ?
            WHERE case_id = ?
        """, (
            title.strip(),
            description.strip(),
            investigator.strip(),
            priority,
            status,
            now,
            case_id
        ))

        return cursor.rowcount > 0


def link_incident_to_case(case_id, incident_id):
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        case_exists = conn.execute(
            "SELECT 1 FROM investigation_cases WHERE case_id = ?",
            (case_id,)
        ).fetchone()

        incident_exists = conn.execute(
            "SELECT 1 FROM incidents WHERE incident_id = ?",
            (incident_id,)
        ).fetchone()

        if not case_exists or not incident_exists:
            return False

        cursor = conn.execute("""
            INSERT OR IGNORE INTO case_incidents (
                case_id, incident_id, linked_at
            )
            VALUES (?, ?, ?)
        """, (case_id, incident_id, now))

        if cursor.rowcount:
            conn.execute("""
                UPDATE investigation_cases
                SET updated_at = ?
                WHERE case_id = ?
            """, (now, case_id))

        return cursor.rowcount > 0


def unlink_incident_from_case(case_id, incident_id):
    with get_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM case_incidents
            WHERE case_id = ? AND incident_id = ?
        """, (case_id, incident_id))

        return cursor.rowcount > 0


def get_case_incidents(case_id):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT i.*, ci.linked_at
            FROM incidents i
            JOIN case_incidents ci
                ON i.incident_id = ci.incident_id
            WHERE ci.case_id = ?
            ORDER BY i.timestamp DESC
        """, (case_id,)).fetchall()

        return [dict(row) for row in rows]


def add_case_note(case_id, note, investigator=""):
    note = note.strip()
    if not note:
        return False

    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        case_exists = conn.execute(
            "SELECT 1 FROM investigation_cases WHERE case_id = ?",
            (case_id,)
        ).fetchone()

        if not case_exists:
            return False

        conn.execute("""
            INSERT INTO case_notes (
                case_id, investigator, note, created_at
            )
            VALUES (?, ?, ?, ?)
        """, (case_id, investigator.strip(), note, now))

        conn.execute("""
            UPDATE investigation_cases
            SET updated_at = ?
            WHERE case_id = ?
        """, (now, case_id))

        return True


def get_case_notes(case_id):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM case_notes
            WHERE case_id = ?
            ORDER BY created_at DESC
        """, (case_id,)).fetchall()

        return [dict(row) for row in rows]

def save_case_report(case_id, report):
    now = datetime.now().isoformat(timespec="seconds")
    report_json = json.dumps(report)

    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS case_reports (
                case_id INTEGER PRIMARY KEY,
                report TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                FOREIGN KEY (case_id)
                    REFERENCES investigation_cases(case_id)
            )
        """)

        conn.execute("""
            INSERT INTO case_reports (case_id, report, generated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(case_id)
            DO UPDATE SET
                report = excluded.report,
                generated_at = excluded.generated_at
        """, (case_id, report_json, now))

        conn.execute("""
            UPDATE investigation_cases
            SET updated_at = ?
            WHERE case_id = ?
        """, (now, case_id))


def get_case_report(case_id):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT report
            FROM case_reports
            WHERE case_id = ?
        """, (case_id,)).fetchone()

        if not row:
            return None

        try:
            return json.loads(row["report"])
        except (ValueError, TypeError):
            return None
