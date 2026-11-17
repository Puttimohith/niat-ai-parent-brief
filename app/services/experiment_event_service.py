from datetime import datetime, timezone
from uuid import uuid4

from app.services import experiment_service
from app.services import tracking_service


ALLOWED_EVENTS = {
    "brief_delivered",
    "brief_viewed",
    "callback_requested",
    "next_step_verified",
}


def initialize_event_database():
    experiment_service.initialize_experiment_database()

    with tracking_service.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiment_events (
                event_id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                lead_id TEXT NOT NULL,
                event_type TEXT NOT NULL
                    CHECK (
                        event_type IN (
                            'brief_delivered',
                            'brief_viewed',
                            'callback_requested',
                            'next_step_verified'
                        )
                    ),
                event_time TEXT NOT NULL,
                verified_by TEXT,
                FOREIGN KEY (experiment_id, lead_id)
                    REFERENCES experiment_assignments(
                        experiment_id, lead_id
                    )
            )
        """)


def record_event(
    lead_id,
    event_type,
    experiment_id="parent_brief_pilot",
    verified_by=None,
):
    if event_type not in ALLOWED_EVENTS:
        raise ValueError("Invalid experiment event")

    if event_type == "next_step_verified":
        if not verified_by or not verified_by.strip():
            raise ValueError(
                "Verified next steps require a reviewer"
            )

    initialize_event_database()

    event_id = str(uuid4())

    with tracking_service.get_connection() as conn:
        assignment = conn.execute("""
            SELECT group_name
            FROM experiment_assignments
            WHERE experiment_id = ?
              AND lead_id = ?
        """, (experiment_id, lead_id)).fetchone()

        if assignment is None:
            raise ValueError(
                "Lead is not assigned to this experiment"
            )

        if (
            event_type in ("brief_delivered", "brief_viewed")
            and assignment["group_name"] != "treatment"
        ):
            raise ValueError(
                "Brief events require treatment assignment"
            )

        conn.execute("""
            INSERT INTO experiment_events (
                event_id,
                experiment_id,
                lead_id,
                event_type,
                event_time,
                verified_by
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            experiment_id,
            lead_id,
            event_type,
            datetime.now(timezone.utc).isoformat(),
            verified_by,
        ))

    return event_id


def get_lead_events(
    lead_id,
    experiment_id="parent_brief_pilot",
):
    initialize_event_database()

    with tracking_service.get_connection() as conn:
        rows = conn.execute("""
            SELECT event_type, event_time, verified_by
            FROM experiment_events
            WHERE lead_id = ?
              AND experiment_id = ?
            ORDER BY event_time
        """, (lead_id, experiment_id)).fetchall()

    return [dict(row) for row in rows]
