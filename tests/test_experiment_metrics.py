from datetime import datetime, timedelta, timezone

import pytest

from app.services import tracking_service
from app.services import experiment_service
from app.services import experiment_schedule_service
from app.services import experiment_consent_service
from app.services import experiment_event_service
from app.services import experiment_metrics_service


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        tracking_service,
        "DB_PATH",
        tmp_path / "metrics_test.db",
    )

    experiment_service.create_experiment()
    experiment_schedule_service.start_experiment()


def make_assigned_lead():
    lead_id = tracking_service.save_lead(
        {
            "preferred_state": "Andhra Pradesh",
            "preferred_institution": "Test Institution",
            "language": "English",
            "annual_budget": "Not decided",
            "concerns": [],
        }
    )

    experiment_consent_service.record_experiment_consent(
        lead_id, True, True
    )

    experiment_service.assign_lead(lead_id)

    return lead_id


def test_empty_metrics(temporary_database):
    metrics = experiment_metrics_service.get_experiment_metrics()

    assert metrics["control"]["assigned"] == 0
    assert metrics["treatment"]["assigned"] == 0


def test_assignment_counted(temporary_database):
    make_assigned_lead()

    metrics = experiment_metrics_service.get_experiment_metrics()

    assert (
        metrics["control"]["assigned"]
        + metrics["treatment"]["assigned"]
    ) == 1


def test_verified_conversion_counted_once(temporary_database):
    lead_id = make_assigned_lead()

    experiment_event_service.record_event(
        lead_id,
        "next_step_verified",
        verified_by="demo_reviewer",
    )

    experiment_event_service.record_event(
        lead_id,
        "next_step_verified",
        verified_by="demo_reviewer",
    )

    metrics = experiment_metrics_service.get_experiment_metrics()

    assert (
        metrics["control"]["verified_conversions"]
        + metrics["treatment"]["verified_conversions"]
    ) == 1


def test_late_conversion_not_counted(temporary_database):
    lead_id = make_assigned_lead()

    experiment_event_service.record_event(
        lead_id,
        "next_step_verified",
        verified_by="demo_reviewer",
    )

    with tracking_service.get_connection() as conn:
        conn.execute("""
            UPDATE experiment_events
            SET event_time = ?
            WHERE lead_id = ?
        """, (
            (
                datetime.now(timezone.utc)
                + timedelta(days=8)
            ).isoformat(),
            lead_id,
        ))

    metrics = experiment_metrics_service.get_experiment_metrics()

    assert (
        metrics["control"]["verified_conversions"]
        + metrics["treatment"]["verified_conversions"]
    ) == 0


def test_invalid_record_type(temporary_database):
    with pytest.raises(ValueError, match="Invalid record type"):
        experiment_metrics_service.get_experiment_metrics(
            record_type="unknown"
        )
