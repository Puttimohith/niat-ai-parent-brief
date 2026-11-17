import pytest

from app.services import experiment_service
from app.services import experiment_consent_service
from app.services import experiment_schedule_service
from app.services import tracking_service


@pytest.fixture
def experiment_database(tmp_path, monkeypatch):
    database = tmp_path / "experiment_test.db"

    monkeypatch.setattr(
        tracking_service,
        "DB_PATH",
        database,
    )

    experiment_service.create_experiment()
    experiment_schedule_service.start_experiment()

    return database


def make_lead(
    record_type="demo",
    consent_granted=True,
    eligibility_confirmed=True,
):
    lead_id = tracking_service.save_lead(
        {
            "preferred_state": "Andhra Pradesh",
            "preferred_institution": "Test Institution",
            "language": "English",
            "annual_budget": "Not specified",
            "concerns": ["Fees"],
        },
        record_type=record_type,
    )

    experiment_consent_service.record_experiment_consent(
        lead_id,
        consent_granted=consent_granted,
        eligibility_confirmed=eligibility_confirmed,
    )

    return lead_id


def test_experiment_creation(experiment_database):
    with tracking_service.get_connection() as conn:
        row = conn.execute("""
            SELECT duration_days, target_per_group
            FROM experiments
            WHERE experiment_id = ?
        """, ("parent_brief_pilot",)).fetchone()

    assert row is not None
    assert row["duration_days"] == 14
    assert row["target_per_group"] == 100


def test_lead_assignment(experiment_database):
    lead_id = make_lead()

    group = experiment_service.assign_lead(lead_id)

    assert group in ("control", "treatment")

    counts = experiment_service.get_experiment_counts()

    assert counts["control"] + counts["treatment"] == 1


def test_assignment_is_idempotent(experiment_database):
    lead_id = make_lead()

    first = experiment_service.assign_lead(lead_id)
    second = experiment_service.assign_lead(lead_id)

    assert first == second

    counts = experiment_service.get_experiment_counts()

    assert counts["control"] + counts["treatment"] == 1


def test_unknown_lead_is_rejected(experiment_database):
    with pytest.raises(ValueError, match="Lead does not exist"):
        experiment_service.assign_lead("missing-lead")


def test_demo_and_real_are_separate(experiment_database):
    demo_lead = make_lead("demo")
    real_lead = make_lead("real")

    experiment_service.assign_lead(demo_lead)
    experiment_service.assign_lead(real_lead)

    demo_counts = experiment_service.get_experiment_counts(
        record_type="demo"
    )
    real_counts = experiment_service.get_experiment_counts(
        record_type="real"
    )

    assert sum(demo_counts.values()) == 1
    assert sum(real_counts.values()) == 1


def test_group_capacity(experiment_database):
    experiment_service.create_experiment(
        experiment_id="small_pilot",
        target_per_group=1,
    )
    experiment_schedule_service.start_experiment("small_pilot")

    leads = [make_lead() for _ in range(2)]

    groups = [
        experiment_service.assign_lead(
            lead_id,
            experiment_id="small_pilot",
        )
        for lead_id in leads
    ]

    assert set(groups) == {"control", "treatment"}

    third_lead = make_lead()

    with pytest.raises(
        ValueError,
        match="Experiment enrollment is full",
    ):
        experiment_service.assign_lead(
            third_lead,
            experiment_id="small_pilot",
        )


def test_assignment_requires_consent(experiment_database):
    lead_id = make_lead(consent_granted=False)

    with pytest.raises(
        ValueError,
        match="Experiment consent and eligibility required",
    ):
        experiment_service.assign_lead(lead_id)


def test_assignment_requires_eligibility(experiment_database):
    lead_id = make_lead(eligibility_confirmed=False)

    with pytest.raises(
        ValueError,
        match="Experiment consent and eligibility required",
    ):
        experiment_service.assign_lead(lead_id)


def test_revoked_consent_blocks_assignment(experiment_database):
    lead_id = make_lead()

    first_group = experiment_service.assign_lead(lead_id)

    assert first_group in ("control", "treatment")

    experiment_consent_service.record_experiment_consent(
        lead_id,
        consent_granted=False,
        eligibility_confirmed=True,
    )

    with pytest.raises(
        ValueError,
        match="Experiment consent and eligibility required",
    ):
        experiment_service.assign_lead(lead_id)
