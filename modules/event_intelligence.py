import networkx as nx


# ----------------------------------
# 1. ANOMALY SCORING
# ----------------------------------

def calculate_anomaly_score(
    movement,
    duration,
    interaction,
    sequence
):
    score = (
        0.25 * movement +
        0.25 * duration +
        0.20 * interaction +
        0.30 * sequence
    )

    return round(score * 100, 2)


# ----------------------------------
# 2. EVENT GRAPH
# ----------------------------------

def create_event_graph(events):

    graph = nx.DiGraph()

    # Create event nodes
    for event in events:
        graph.add_node(
            event["event_id"],
            action=event["action"],
            timestamp=event["timestamp"]
        )

    # Connect events in chronological order
    sorted_events = sorted(
        events,
        key=lambda event: event["timestamp"]
    )

    for i in range(len(sorted_events) - 1):
        graph.add_edge(
            sorted_events[i]["event_id"],
            sorted_events[i + 1]["event_id"],
            relationship="followed_by"
        )

    return graph


# ----------------------------------
# 3. SIMPLE SEQUENCE NOVELTY
# ----------------------------------

def check_sequence_novelty(
    observed_sequence,
    known_sequences
):
    if tuple(observed_sequence) in known_sequences:
        return 0.0

    return 1.0


# ----------------------------------
# 4. GENERATE EXPLANATION
# ----------------------------------

def generate_explanation(signals, score):

    reasons = []

    if signals["movement"] >= 0.7:
        reasons.append("Movement pattern differs from baseline")

    if signals["duration"] >= 0.7:
        reasons.append("Duration differs from baseline")

    if signals["interaction"] >= 0.7:
        reasons.append("Unusual object interaction observed")

    if signals["sequence"] >= 0.7:
        reasons.append("Unfamiliar event sequence observed")

    if not reasons:
        reasons.append("No strong anomaly signals found")

    return {
        "anomaly_score": score,
        "reasons": reasons,
        "review_required": score >= 60
    }


# ----------------------------------
# 5. TEST OUR PROTOTYPE
# ----------------------------------

if __name__ == "__main__":

    # Example signals (simulated for testing)
    signals = {
        "movement": 0.3,
        "duration": 0.9,
        "interaction": 0.8,
        "sequence": 0.9
    }

    score = calculate_anomaly_score(
        signals["movement"],
        signals["duration"],
        signals["interaction"],
        signals["sequence"]
    )

    explanation = generate_explanation(
        signals,
        score
    )

    print("\n--- NEMESIS-X EVENT INTELLIGENCE ---")
    print("Anomaly Score:", score)
    print("Reasons:")

    for reason in explanation["reasons"]:
        print("-", reason)

    print("Review Required:", explanation["review_required"])

    # Example events
    sample_events = [
        {
            "event_id": "E1",
            "action": "person_enters",
            "timestamp": 10
        },
        {
            "event_id": "E2",
            "action": "object_interaction",
            "timestamp": 15
        },
        {
            "event_id": "E3",
            "action": "object_placed",
            "timestamp": 20
        },
        {
            "event_id": "E4",
            "action": "person_moves_away",
            "timestamp": 30
        },
        {
            "event_id": "E5",
            "action": "object_remains",
            "timestamp": 60
        }
    ]

    graph = create_event_graph(sample_events)

    print("\n--- EVENT GRAPH ---")
    print("Nodes:", list(graph.nodes(data=True)))
    print("Edges:", list(graph.edges(data=True)))