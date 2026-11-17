import pytest

from app.services import tracking_service
from app.services import experiment_service
from app.services import experiment_schedule_service
from app.services import experiment_consent_service
from app.services import brief_experiment_bridge as bridge


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        tracking_service,
        "DB_PATH",
        tmp_path / "bridge_test.db",
    )


def make_lead():
    return tracking_service.save_lead({
        "preferred_state": "Andhra Pradesh",
        "preferred_institution": "Demo Institution",
        "language": "English",
        "annual_budget": "Not decided",
        "concerns": [],
    })


def test_unassigned_lead_ignored(temporary_database):
    lead_id = make_lead()

    assert bridge.record_brief_experiment_event(
        lead_id,
        "brief_viewed",
    ) is False


def test_invalid_event_rejected(temporary_database):
    lead_id = make_lead()

    with pytest.raises(
        ValueError,
        match="Unsupported brief event",
    ):
        bridge.record_brief_experiment_event(
            lead_id,
            "next_step_verified",
        )


def test_treatment_event_recorded(temporary_database):
    experiment_service.create_experiment()
    experiment_schedule_service.start_experiment()

    lead_id = make_lead()

    experiment_consent_service.record_experiment_consent(
        lead_id,
        True,
        True,
    )

    experiment_service.assign_lead(lead_id)

    # Force the assignment to treatment for this
    # deterministic integration test.
    with tracking_service.get_connection() as conn:
        conn.execute("""
            UPDATE experiment_assignments
            SET group_name = 'treatment'
            WHERE lead_id = ?
        """, (lead_id,))

    assert bridge.record_brief_experiment_event(
        lead_id,
        "brief_viewed",
    ) is True


def test_control_event_ignored(temporary_database):
    experiment_service.create_experiment()
    experiment_schedule_service.start_experiment()

    lead_id = make_lead()

    experiment_consent_service.record_experiment_consent(
        lead_id,
        True,
        True,
    )

    experiment_service.assign_lead(lead_id)

    with tracking_service.get_connection() as conn:
        conn.execute("""
            UPDATE experiment_assignments
            SET group_name = 'control'
            WHERE lead_id = ?
        """, (lead_id,))

    assert bridge.record_brief_experiment_event(
        lead_id,
        "brief_viewed",
    ) is False
