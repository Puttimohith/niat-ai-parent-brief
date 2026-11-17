import pytest

from app.services import tracking_service
from app.services import experiment_service
from app.services import experiment_schedule_service
from app.services import experiment_consent_service
from app.services import experiment_event_service as events


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        tracking_service,
        "DB_PATH",
        tmp_path / "events_test.db",
    )

    experiment_service.create_experiment()
    experiment_schedule_service.start_experiment()


def assigned_lead():
    lead_id = tracking_service.save_lead(
        {
            "preferred_state": "Andhra Pradesh",
            "preferred_institution": "Test Institution",
            "language": "English",
            "annual_budget": "Not decided",
            "concerns": [],
        },
        record_type="demo",
    )

    experiment_consent_service.record_experiment_consent(
        lead_id,
        True,
        True,
    )

    group = experiment_service.assign_lead(lead_id)

    return lead_id, group


def test_callback_event(temporary_database):
    lead_id, _ = assigned_lead()

    events.record_event(lead_id, "callback_requested")

    result = events.get_lead_events(lead_id)

    assert len(result) == 1
    assert result[0]["event_type"] == "callback_requested"


def test_verified_step_requires_reviewer(temporary_database):
    lead_id, _ = assigned_lead()

    with pytest.raises(
        ValueError,
        match="require a reviewer",
    ):
        events.record_event(
            lead_id,
            "next_step_verified",
        )


def test_verified_step_recorded(temporary_database):
    lead_id, _ = assigned_lead()

    events.record_event(
        lead_id,
        "next_step_verified",
        verified_by="demo_reviewer",
    )

    result = events.get_lead_events(lead_id)

    assert result[0]["verified_by"] == "demo_reviewer"


def test_invalid_event_rejected(temporary_database):
    lead_id, _ = assigned_lead()

    with pytest.raises(
        ValueError,
        match="Invalid experiment event",
    ):
        events.record_event(lead_id, "purchase_completed")


def test_unassigned_lead_rejected(temporary_database):
    lead_id = tracking_service.save_lead(
        {
            "preferred_state": "Telangana",
            "concerns": [],
        }
    )

    with pytest.raises(
        ValueError,
        match="not assigned",
    ):
        events.record_event(lead_id, "callback_requested")


def test_brief_event_requires_treatment(temporary_database):
    lead_id, group = assigned_lead()

    if group == "control":
        with pytest.raises(
            ValueError,
            match="treatment assignment",
        ):
            events.record_event(
                lead_id,
                "brief_delivered",
            )
    else:
        events.record_event(
            lead_id,
            "brief_delivered",
        )

        result = events.get_lead_events(lead_id)

        assert result[0]["event_type"] == "brief_delivered"
