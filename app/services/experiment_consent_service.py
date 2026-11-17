from datetime import datetime, timezone

from app.services import tracking_service


def initialize_consent_database():
    tracking_service.initialize_database()

    with tracking_service.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiment_consent (
                lead_id TEXT PRIMARY KEY,
                consent_granted INTEGER NOT NULL
                    CHECK (consent_granted IN (0, 1)),
                eligibility_confirmed INTEGER NOT NULL
                    CHECK (eligibility_confirmed IN (0, 1)),
                consent_recorded_at TEXT NOT NULL,
                FOREIGN KEY (lead_id)
                    REFERENCES leads(lead_id)
            )
        """)


def record_experiment_consent(
    lead_id,
    consent_granted,
    eligibility_confirmed,
):
    if not isinstance(consent_granted, bool):
        raise ValueError("Consent must be a boolean")

    if not isinstance(eligibility_confirmed, bool):
        raise ValueError("Eligibility must be a boolean")

    initialize_consent_database()

    with tracking_service.get_connection() as conn:
        lead = conn.execute(
            "SELECT lead_id FROM leads WHERE lead_id = ?",
            (lead_id,),
        ).fetchone()

        if lead is None:
            raise ValueError("Lead does not exist")

        conn.execute("""
            INSERT INTO experiment_consent (
                lead_id,
                consent_granted,
                eligibility_confirmed,
                consent_recorded_at
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(lead_id)
            DO UPDATE SET
                consent_granted = excluded.consent_granted,
                eligibility_confirmed = excluded.eligibility_confirmed,
                consent_recorded_at = excluded.consent_recorded_at
        """, (
            lead_id,
            int(consent_granted),
            int(eligibility_confirmed),
            datetime.now(timezone.utc).isoformat(),
        ))


def is_eligible_and_consented(lead_id):
    initialize_consent_database()

    with tracking_service.get_connection() as conn:
        row = conn.execute("""
            SELECT consent_granted, eligibility_confirmed
            FROM experiment_consent
            WHERE lead_id = ?
        """, (lead_id,)).fetchone()

    return bool(
        row
        and row["consent_granted"] == 1
        and row["eligibility_confirmed"] == 1
    )
