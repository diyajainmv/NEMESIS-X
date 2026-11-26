
from datetime import datetime
from itertools import combinations


def parse_time(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


def safe_score(value):
    try:
        if value is None:
            return None
        return max(0.0, min(float(value), 1.0))
    except (ValueError, TypeError):
        return None


def analyze_case(incidents):
    """
    Correlates existing incident records.
    This is explainable rule-based analysis, not identity recognition.
    """

    incidents = sorted(
        incidents,
        key=lambda item: parse_time(item.get("timestamp"))
        or datetime.max
    )

    if not incidents:
        return {
            "summary": "No incidents are linked to this case.",
            "incident_count": 0,
            "timeline": [],
            "connections": [],
            "high_anomalies": [],
            "warnings": ["Add incidents before analyzing this case."],
            "recommendations": ["Link relevant incidents to this case."],
        }

    timeline = []
    connections = []
    high_anomalies = []
    warnings = []

    # ----------------------------------
    # BUILD CHRONOLOGICAL TIMELINE
    # ----------------------------------

    for incident in incidents:

        timeline.append({
            "incident_id": incident.get("incident_id"),
            "event_type": incident.get("event_type", "Unknown"),
            "timestamp": incident.get("timestamp"),
            "location": incident.get("camera_location") or "Unknown",
            "priority": incident.get("priority") or "Unknown",
            "status": incident.get("status") or "Unknown",
            "explanation": incident.get("explanation") or "",
            "video_timestamp": incident.get("video_timestamp"),
            "evidence": incident.get("evidence"),
            "evidence_frames": incident.get("evidence_frames"),
        })

        score = safe_score(incident.get("anomaly_score"))

        if score is not None and score >= 0.70:
            high_anomalies.append({
                "incident_id": incident.get("incident_id"),
                "score": score,
                "event_type": incident.get("event_type"),
            })

    # ----------------------------------
    # FIND POSSIBLE INCIDENT CONNECTIONS
    # ----------------------------------

    for first, second in combinations(incidents, 2):

        reasons = []
        score = 0.0

        first_time = parse_time(first.get("timestamp"))
        second_time = parse_time(second.get("timestamp"))

        # Same analysis run: strong contextual connection,
        # but does not prove the events are related.
        first_run = first.get("run_id")
        second_run = second.get("run_id")

        if first_run and second_run and first_run == second_run:
            score += 0.40
            reasons.append(
                "Both incidents originated from the same video analysis run."
            )

        # Temporal proximity
        if first_time and second_time:
            difference = abs(
                (second_time - first_time).total_seconds()
            )

            if difference <= 60:
                score += 0.30
                reasons.append(
                    "Events occurred within one minute of each other."
                )
            elif difference <= 300:
                score += 0.20
                reasons.append(
                    "Events occurred within five minutes of each other."
                )
            elif difference <= 900:
                score += 0.10
                reasons.append(
                    "Events occurred within fifteen minutes of each other."
                )

        # Same camera/location
        first_location = (
            first.get("camera_location") or ""
        ).strip().lower()

        second_location = (
            second.get("camera_location") or ""
        ).strip().lower()

        if (
            first_location
            and second_location
            and first_location == second_location
        ):
            score += 0.15
            reasons.append(
                "Both incidents were recorded at the same location."
            )

        # Same event category
        first_type = (
            first.get("event_type") or ""
        ).strip().lower()

        second_type = (
            second.get("event_type") or ""
        ).strip().lower()

        if first_type and first_type == second_type:
            score += 0.15
            reasons.append(
                "Both incidents have the same event category."
            )

        score = min(score, 1.0)

        if score >= 0.30:

            if score >= 0.70:
                strength = "Strong contextual match"
            elif score >= 0.45:
                strength = "Moderate contextual match"
            else:
                strength = "Weak contextual match"

            connections.append({
                "incident_a": first.get("incident_id"),
                "incident_b": second.get("incident_id"),
                "score": round(score, 2),
                "strength": strength,
                "reasons": reasons,
                "warning": (
                    "This is a contextual correlation, "
                    "not proof of a common person or cause."
                ),
            })

    # ----------------------------------
    # WARNINGS AND RECOMMENDATIONS
    # ----------------------------------

    if len(incidents) == 1:
        warnings.append(
            "Only one incident is linked. Cross-incident "
            "correlation is not possible yet."
        )

    if any(not item.get("evidence") for item in incidents):
        warnings.append(
            "Some incidents do not have a linked video evidence file."
        )

    if any(not item.get("explanation") for item in incidents):
        warnings.append(
            "Some incidents do not contain an AI event explanation."
        )

    if not connections and len(incidents) > 1:
        warnings.append(
            "No strong contextual relationships were found "
            "using the available incident metadata."
        )

    recommendations = []

    if connections:
        recommendations.append(
            "Review the linked incident pairs and verify their "
            "supporting video evidence."
        )

    if high_anomalies:
        recommendations.append(
            "Prioritize reviewing incidents with high anomaly scores."
        )

    if any(not item.get("evidence") for item in incidents):
        recommendations.append(
            "Attach or recover missing video evidence where possible."
        )

    recommendations.append(
        "Have an investigator verify all possible connections "
        "before drawing conclusions."
    )

    # ----------------------------------
    # CASE SUMMARY
    # ----------------------------------

    summary = (
        f"Analysis reviewed {len(incidents)} incidents and identified "
        f"{len(connections)} possible contextual relationships. "
        f"{len(high_anomalies)} incidents have anomaly scores of "
        f"0.70 or higher."
    )

    return {
        "summary": summary,
        "incident_count": len(incidents),
        "timeline": timeline,
        "connections": connections,
        "high_anomalies": high_anomalies,
        "warnings": warnings,
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "analysis_type": "Rule-based incident correlation",
    }
