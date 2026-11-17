import secrets
import sqlite3
from datetime import datetime, timezone

from app.services import tracking_service


def get_connection():
    return tracking_service.get_connection()


def initialize_experiment_database():
    tracking_service.initialize_database()

    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                experiment_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                target_per_group INTEGER NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiment_assignments (
                experiment_id TEXT NOT NULL,
                lead_id TEXT NOT NULL,
                group_name TEXT NOT NULL
                    CHECK (group_name IN ('control', 'treatment')),
                assigned_at TEXT NOT NULL,
                PRIMARY KEY (experiment_id, lead_id),
                FOREIGN KEY (experiment_id)
                    REFERENCES experiments(experiment_id),
                FOREIGN KEY (lead_id)
                    REFERENCES leads(lead_id)
            )
        """)


def create_experiment(
    experiment_id="parent_brief_pilot",
    experiment_name="AI Parent Decision Brief Pilot",
    duration_days=14,
    target_per_group=100,
):
    initialize_experiment_database()

    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO experiments (
                experiment_id,
                experiment_name,
                created_at,
                duration_days,
                target_per_group
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            experiment_id,
            experiment_name,
            datetime.now(timezone.utc).isoformat(),
            duration_days,
            target_per_group,
        ))

    return experiment_id


def assign_lead(
    lead_id,
    experiment_id="parent_brief_pilot",
):
    initialize_experiment_database()

    with get_connection() as conn:
        # Acquire a write lock before checking capacity.
        conn.execute("BEGIN IMMEDIATE")

        lead = conn.execute("""
            SELECT lead_id, record_type
            FROM leads
            WHERE lead_id = ?
        """, (lead_id,)).fetchone()

        if lead is None:
            raise ValueError("Lead does not exist")

        consent = conn.execute("""
            SELECT consent_granted, eligibility_confirmed
            FROM experiment_consent
            WHERE lead_id = ?
        """, (lead_id,)).fetchone() if conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table'
              AND name = 'experiment_consent'
        """).fetchone() else None

        if (
            consent is None
            or consent["consent_granted"] != 1
            or consent["eligibility_confirmed"] != 1
        ):
            raise ValueError(
                "Experiment consent and eligibility required"
            )

        experiment = conn.execute("""
            SELECT experiment_id, target_per_group,
                   started_at, ended_at
            FROM experiments
            WHERE experiment_id = ?
        """, (experiment_id,)).fetchone()

        if experiment is None:
            raise ValueError("Experiment does not exist")

        if (
            experiment["started_at"] is None
            or experiment["ended_at"] is None
        ):
            raise ValueError("Experiment is not active")

        now = datetime.now(timezone.utc)
        start = datetime.fromisoformat(
            experiment["started_at"]
        )
        end = datetime.fromisoformat(
            experiment["ended_at"]
        )

        if not (start <= now < end):
            raise ValueError("Experiment is not active")

        existing = conn.execute("""
            SELECT group_name
            FROM experiment_assignments
            WHERE experiment_id = ?
              AND lead_id = ?
        """, (experiment_id, lead_id)).fetchone()

        if existing:
            return existing["group_name"]

        counts = {
            row["group_name"]: row["total"]
            for row in conn.execute("""
                SELECT a.group_name, COUNT(*) AS total
                FROM experiment_assignments a
                JOIN leads l ON l.lead_id = a.lead_id
                WHERE a.experiment_id = ?
                  AND l.record_type = ?
                GROUP BY a.group_name
            """, (experiment_id, lead["record_type"]))
        }

        control_count = counts.get("control", 0)
        treatment_count = counts.get("treatment", 0)
        target = experiment["target_per_group"]

        if control_count >= target and treatment_count >= target:
            raise ValueError("Experiment enrollment is full")

        if control_count >= target:
            group = "treatment"
        elif treatment_count >= target:
            group = "control"
        else:
            group = secrets.choice(["control", "treatment"])

        conn.execute("""
            INSERT INTO experiment_assignments (
                experiment_id,
                lead_id,
                group_name,
                assigned_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            experiment_id,
            lead_id,
            group,
            datetime.now(timezone.utc).isoformat(),
        ))

    return group


def get_experiment_counts(
    experiment_id="parent_brief_pilot",
    record_type="demo",
):
    initialize_experiment_database()

    if record_type not in ("demo", "real"):
        raise ValueError("Invalid record type")

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT a.group_name, COUNT(*) AS total
            FROM experiment_assignments a
            JOIN leads l ON l.lead_id = a.lead_id
            WHERE a.experiment_id = ?
              AND l.record_type = ?
            GROUP BY a.group_name
        """, (experiment_id, record_type)).fetchall()

    counts = {
        "control": 0,
        "treatment": 0,
    }

    for row in rows:
        counts[row["group_name"]] = row["total"]

    return counts
