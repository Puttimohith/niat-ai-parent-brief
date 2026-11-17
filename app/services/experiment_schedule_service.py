from datetime import datetime, timedelta, timezone

from app.services import experiment_service


def initialize_schedule_database():
    experiment_service.initialize_experiment_database()

    with experiment_service.get_connection() as conn:
        columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(experiments)"
            )
        }

        if "started_at" not in columns:
            conn.execute("""
                ALTER TABLE experiments
                ADD COLUMN started_at TEXT
            """)

        if "ended_at" not in columns:
            conn.execute("""
                ALTER TABLE experiments
                ADD COLUMN ended_at TEXT
            """)


def start_experiment(experiment_id="parent_brief_pilot"):
    initialize_schedule_database()

    with experiment_service.get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")

        experiment = conn.execute("""
            SELECT started_at, duration_days
            FROM experiments
            WHERE experiment_id = ?
        """, (experiment_id,)).fetchone()

        if experiment is None:
            raise ValueError("Experiment does not exist")

        if experiment["started_at"] is not None:
            raise ValueError("Experiment has already started")

        now = datetime.now(timezone.utc)
        end = now + timedelta(
            days=experiment["duration_days"]
        )

        conn.execute("""
            UPDATE experiments
            SET started_at = ?, ended_at = ?
            WHERE experiment_id = ?
        """, (
            now.isoformat(),
            end.isoformat(),
            experiment_id,
        ))

    return {
        "started_at": now.isoformat(),
        "ended_at": end.isoformat(),
    }


def get_experiment_status(experiment_id="parent_brief_pilot"):
    initialize_schedule_database()

    with experiment_service.get_connection() as conn:
        experiment = conn.execute("""
            SELECT started_at, ended_at
            FROM experiments
            WHERE experiment_id = ?
        """, (experiment_id,)).fetchone()

    if experiment is None:
        raise ValueError("Experiment does not exist")

    if experiment["started_at"] is None:
        return "not_started"

    now = datetime.now(timezone.utc)

    start = datetime.fromisoformat(
        experiment["started_at"]
    )
    end = datetime.fromisoformat(
        experiment["ended_at"]
    )

    if now < start:
        return "scheduled"

    if now >= end:
        return "completed"

    return "active"
