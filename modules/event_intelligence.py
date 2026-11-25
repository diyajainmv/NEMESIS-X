"""Member 3: analyze Member 2's SQLite tracking observations.

Run from the repository root:
    python modules/event_intelligence.py

Or provide a database path:
    python modules/event_intelligence.py path/to/tracking_history.db

Events follow docs/DATA_CONTRACT.md. Scores are normalized to [0, 1].
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import networkx as nx


DEFAULT_DB = "data/tracking_history.db"
PERSON_CLASSES = {"person", "human"}
BAG_CLASSES = {"backpack", "handbag", "suitcase", "bag", "luggage", "package"}
INTERACTION_DISTANCE_PX = 100.0
STATIONARY_DISTANCE_PX = 25.0
MIN_UNATTENDED_SECONDS = 10.0
MAX_OBSERVATION_GAP_SECONDS = 5.0


def _score(value: float) -> float:
    """Clamp and round an anomaly score to the contract's [0, 1] range."""
    return round(max(0.0, min(1.0, float(value))), 3)


def _read_sqlite(path: str | Path = DEFAULT_DB) -> List[Dict[str, Any]]:
    """Read actual tracked detections from Member 2's observations table."""
    db = Path(path)
    if not db.is_file():
        raise FileNotFoundError(f"Tracking database not found: {db}")
    with sqlite3.connect(str(db)) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(observations)")}
        required = {"frame_number", "track_id", "class_name", "x1", "y1", "x2", "y2", "center_x", "center_y", "timestamp"}
        missing = required - columns
        if missing:
            raise ValueError("observations table is missing columns: " + ", ".join(sorted(missing)))
        rows = connection.execute(
            """SELECT frame_number, track_id, class_name, x1, y1, x2, y2,
                      center_x, center_y, timestamp
               FROM observations
               ORDER BY timestamp, frame_number, track_id"""
        ).fetchall()
    if not rows:
        raise ValueError("The observations table is empty. Run Member 2's tracking pipeline first.")

    frames: Dict[Tuple[int, float], Dict[str, Any]] = {}
    for frame_no, track_id, label, x1, y1, x2, y2, cx, cy, timestamp in rows:
        frame_no, timestamp = int(frame_no), float(timestamp)
        if not math.isfinite(timestamp) or timestamp < 0:
            continue
        frame = frames.setdefault((frame_no, timestamp), {
            "frame_number": frame_no, "timestamp": timestamp, "tracked_objects": []
        })
        frame["tracked_objects"].append({
            "track_id": track_id,
            "class_name": str(label).strip().lower(),
            "bbox": [float(x1), float(y1), float(x2), float(y2)],
            "center": [float(cx), float(cy)],
        })
    return sorted(frames.values(), key=lambda f: (f["timestamp"], f["frame_number"]))


def _center(obj: Mapping[str, Any]) -> Tuple[float, float]:
    c = obj.get("center")
    if c and len(c) == 2:
        return float(c[0]), float(c[1])
    x1, y1, x2, y2 = obj["bbox"]
    return (float(x1 + x2) / 2, float(y1 + y2) / 2)


def _distance(a: Sequence[float], b: Sequence[float]) -> float:
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def _box_gap(a: Mapping[str, Any], b: Mapping[str, Any]) -> float:
    """Minimum pixel gap between boxes, falling back to center distance."""
    if not a.get("bbox") or not b.get("bbox"):
        return _distance(_center(a), _center(b))
    ax1, ay1, ax2, ay2 = a["bbox"]
    bx1, by1, bx2, by2 = b["bbox"]
    dx = max(float(ax1) - float(bx2), float(bx1) - float(ax2), 0.0)
    dy = max(float(ay1) - float(by2), float(by1) - float(ay2), 0.0)
    return math.hypot(dx, dy)


def _tracks(frames: Sequence[Mapping[str, Any]]) -> Dict[Any, List[Dict[str, Any]]]:
    result: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for frame in frames:
        for obj in frame["tracked_objects"]:
            result[obj["track_id"]].append({
                **obj,
                "timestamp": float(frame["timestamp"]),
                "frame_number": int(frame["frame_number"]),
                "center": list(_center(obj)),
            })
    for observations in result.values():
        observations.sort(key=lambda o: (o["timestamp"], o["frame_number"]))
    return dict(result)


def calculate_track_metrics(track: Sequence[Mapping[str, Any]]) -> Dict[str, float]:
    """Calculate observed path length (pixels), displacement and duration."""
    if not track:
        return {"movement_pixels": 0.0, "displacement_pixels": 0.0, "duration_seconds": 0.0, "max_gap_seconds": 0.0}
    points = [_center(row) for row in track]
    times = [float(row["timestamp"]) for row in track]
    movement = sum(_distance(a, b) for a, b in zip(points, points[1:]))
    gaps = [max(0.0, b - a) for a, b in zip(times, times[1:])]
    return {
        "movement_pixels": round(movement, 2),
        "displacement_pixels": round(_distance(points[0], points[-1]), 2),
        "duration_seconds": round(max(times) - min(times), 3),
        "max_gap_seconds": round(max(gaps, default=0.0), 3),
    }


def _event(event_id: str, kind: str, timestamp: float, track_ids: Iterable[Any], score: float,
           explanation: str, frames: Iterable[int]) -> Dict[str, Any]:
    """Build exactly the agreed Member 3 event fields."""
    return {
        "event_id": event_id,
        "event_type": kind,
        "timestamp": round(float(timestamp), 3),
        "track_ids": list(track_ids),
        "anomaly_score": _score(score),
        "explanation": explanation,
        "evidence_frames": sorted({int(f) for f in frames}),
    }


def analyze_frames(frames: Sequence[Mapping[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Derive movement, duration, pair interactions and sequences from observations."""
    tracks = _tracks(frames)
    events: List[Dict[str, Any]] = []
    metrics: Dict[str, Dict[str, float]] = {}

    # Actual per-track movement and duration, with evidence from observed frames.
    for track_id, observations in tracks.items():
        if len(observations) < 2:
            continue
        metric = calculate_track_metrics(observations)
        metrics[str(track_id)] = metric
        if metric["duration_seconds"] <= 0 or metric["max_gap_seconds"] > MAX_OBSERVATION_GAP_SECONDS:
            continue
        speed = metric["movement_pixels"] / metric["duration_seconds"]
        # Movement event score rises with speed, capped at 300 px/s.
        events.append(_event(
            "", "track_movement", observations[-1]["timestamp"], [track_id],
            speed / 300.0,
            f"Track {track_id} moved {metric['movement_pixels']:.1f} pixels over {metric['duration_seconds']:.1f} seconds.",
            (observations[0]["frame_number"], observations[-1]["frame_number"]),
        ))

    # Pairwise object interaction: objects whose boxes come within a pixel threshold.
    close_samples: Dict[Tuple[Any, Any], List[Tuple[float, int, float]]] = defaultdict(list)
    for frame in frames:
        objects = frame["tracked_objects"]
        for i, first in enumerate(objects):
            for second in objects[i + 1:]:
                if first["track_id"] == second["track_id"]:
                    continue
                gap = _box_gap(first, second)
                if gap <= INTERACTION_DISTANCE_PX:
                    pair = tuple(sorted((first["track_id"], second["track_id"]), key=str))
                    close_samples[pair].append((float(frame["timestamp"]), int(frame["frame_number"]), gap))

    for (id_a, id_b), samples in close_samples.items():
        samples.sort()
        # Collapse adjacent close detections into one interaction episode.
        groups: List[List[Tuple[float, int, float]]] = []
        for sample in samples:
            if not groups or sample[0] - groups[-1][-1][0] > MAX_OBSERVATION_GAP_SECONDS:
                groups.append([sample])
            else:
                groups[-1].append(sample)
        for group in groups:
            duration = max(0.0, group[-1][0] - group[0][0])
            mean_gap = sum(item[2] for item in group) / len(group)
            # Longer and closer observed contacts receive a higher review score.
            score = 0.5 * min(duration / 10.0, 1.0) + 0.5 * (1.0 - min(mean_gap / INTERACTION_DISTANCE_PX, 1.0))
            class_a = next((o["class_name"] for o in tracks[id_a]), "object") if id_a in tracks else "object"
            class_b = next((o["class_name"] for o in tracks[id_b]), "object") if id_b in tracks else "object"
            events.append(_event(
                "", "object_interaction", group[-1][0], [id_a, id_b], score,
                f"Tracked {class_a} {id_a} and {class_b} {id_b} were within {INTERACTION_DISTANCE_PX:.0f} pixels for {duration:.1f} observed seconds.",
                (item[1] for item in group),
            ))

    # Left-object event from real observations: person close, then away, while
    # a bag-like track remains still and continuously observed for the interval.
    people = {tid: obs for tid, obs in tracks.items() if obs and obs[0]["class_name"] in PERSON_CLASSES}
    bags = {tid: obs for tid, obs in tracks.items() if obs and obs[0]["class_name"] in BAG_CLASSES}
    for bag_id, bag_obs in bags.items():
        for person_id, person_obs in people.items():
            bag_start = bag_obs[0]
            near = next((p for p in person_obs if p["timestamp"] >= bag_start["timestamp"] and _box_gap(p, bag_start) <= INTERACTION_DISTANCE_PX), None)
            if near is None:
                continue
            away = next((p for p in person_obs if p["timestamp"] > near["timestamp"] and _box_gap(p, bag_start) >= 150.0), None)
            if away is None:
                continue
            confirmation = next((b for b in bag_obs if b["timestamp"] - away["timestamp"] >= MIN_UNATTENDED_SECONDS), None)
            if confirmation is None:
                continue
            bag_window = [b for b in bag_obs if away["timestamp"] <= b["timestamp"] <= confirmation["timestamp"]]
            if len(bag_window) < 2 or any(y["timestamp"] - x["timestamp"] > MAX_OBSERVATION_GAP_SECONDS for x, y in zip(bag_window, bag_window[1:])):
                continue
            displacement = max(_distance(_center(b), _center(bag_start)) for b in bag_window)
            if displacement > STATIONARY_DISTANCE_PX:
                continue
            returned = any(p["timestamp"] > away["timestamp"] and p["timestamp"] <= confirmation["timestamp"] and _box_gap(p, bag_start) <= INTERACTION_DISTANCE_PX for p in person_obs)
            if returned:
                continue
            duration = confirmation["timestamp"] - away["timestamp"]
            score = 0.4 * (1 - min(displacement / STATIONARY_DISTANCE_PX, 1.0)) + 0.3 * min(duration / MIN_UNATTENDED_SECONDS, 1.0) + 0.3 * min(_box_gap(away, bag_start) / 150.0, 1.0)
            events.append(_event(
                "", "unattended_object", confirmation["timestamp"], [person_id, bag_id], score,
                f"Tracked {bag_obs[0]['class_name']} {bag_id} stayed within {displacement:.1f} pixels for {duration:.1f} seconds after person {person_id} moved away. Human review is required.",
                (near["frame_number"], away["frame_number"], confirmation["frame_number"]),
            ))

    # Sequence order is derived from the timestamps/evidence generated above.
    events.sort(key=lambda e: (e["timestamp"], e["event_type"], str(e["track_ids"])))
    for index, event in enumerate(events, 1):
        event["event_id"] = f"EVT{index:03d}"
    sequence = [{"event_id": e["event_id"], "event_type": e["event_type"], "timestamp": e["timestamp"], "track_ids": e["track_ids"]} for e in events]
    return events, {"track_metrics": metrics, "event_sequence": sequence}


def create_event_graph(events: Sequence[Mapping[str, Any]]) -> nx.DiGraph:
    graph = nx.DiGraph()
    ordered = sorted(events, key=lambda e: (e["timestamp"], e["event_id"]))
    for event in ordered:
        graph.add_node(event["event_id"], **dict(event))
    for first, second in zip(ordered, ordered[1:]):
        graph.add_edge(first["event_id"], second["event_id"], relationship="followed_by",
                       elapsed_seconds=round(float(second["timestamp"]) - float(first["timestamp"]), 3))
    return graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Member 3 Event Intelligence from Member 2 SQLite observations")
    parser.add_argument("database_path", nargs="?", default=DEFAULT_DB, help="SQLite tracking database")
    args = parser.parse_args()
    frames = _read_sqlite(args.database_path)
    events, analysis = analyze_frames(frames)
    graph = create_event_graph(events)
    print(json.dumps({
        "events": events,
        "event_graph": {
            "nodes": [{"event_id": node, **attrs} for node, attrs in graph.nodes(data=True)],
            "edges": [{"source": src, "target": dst, **attrs} for src, dst, attrs in graph.edges(data=True)],
        },
        "analysis": analysis,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
