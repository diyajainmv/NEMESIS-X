
from modules.incident_manager import (
    init_db,
    add_incident,
    get_incidents,
    update_status
)

# Initialize database
init_db()

# Insert sample incident
incident_id = add_incident(
    "Unusual Activity",
    "2026-11-25 18:00:00",
    "Camera 01",
    "High",
    "sample.avi"
)

print("Incident created:", incident_id)

# Display incidents
print("\nAll Incidents:")

for incident in get_incidents():
    print(incident)

# Update status
update_status(incident_id, "Under Review")

print("\nUpdated Incidents:")

for incident in get_incidents():
    print(incident)
