from datetime import datetime, timedelta, timezone

import pytest

from app.services import tracking_service
from app.services import experiment_service
from app.services import experiment_schedule_service
from app.services import experiment_consent_service


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        tracking_service,
        "DB_PATH",
        tmp_path / "window_test.db",
    )

    experiment_service.create_experiment()


def create_consented_lead():
    lead_id = tracking_service.save_lead(
        {
            "preferred_state": "Andhra Pradesh",
            "preferred_institution": "Test Institution",
            "language": "English",
            "annual_budget": "Not decided",
            "concerns": ["Fees"],
        },
        record_type="demo",
    )

    experiment_consent_service.record_experiment_consent(
        lead_id,
        consent_granted=True,
        eligibility_confirmed=True,
    )

    return lead_id


def test_enrollment_before_start_rejected(temporary_database):
    lead_id = create_consented_lead()

    # Create schedule columns without starting the pilot.
    experiment_schedule_service.initialize_schedule_database()

    with pytest.raises(
        ValueError,
        match="Experiment is not active",
    ):
        experiment_service.assign_lead(lead_id)


def test_enrollment_after_end_rejected(temporary_database):
    lead_id = create_consented_lead()

    experiment_schedule_service.start_experiment()

    now = datetime.now(timezone.utc)

    expired_start = now - timedelta(days=15)
    expired_end = now - timedelta(days=1)

    with tracking_service.get_connection() as conn:
        conn.execute("""
            UPDATE experiments
            SET started_at = ?, ended_at = ?
            WHERE experiment_id = ?
        """, (
            expired_start.isoformat(),
            expired_end.isoformat(),
            "parent_brief_pilot",
        ))

    with pytest.raises(
        ValueError,
        match="Experiment is not active",
    ):
        experiment_service.assign_lead(lead_id)


def test_enrollment_during_active_window(temporary_database):
    lead_id = create_consented_lead()

    experiment_schedule_service.start_experiment()

    group = experiment_service.assign_lead(lead_id)

    assert group in ("control", "treatment")

    counts = experiment_service.get_experiment_counts()

    assert sum(counts.values()) == 1
