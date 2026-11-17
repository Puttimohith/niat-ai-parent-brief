import pytest

from app.services import tracking_service
from app.services import experiment_consent_service as consent


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        tracking_service,
        "DB_PATH",
        tmp_path / "consent_test.db",
    )


def make_lead():
    return tracking_service.save_lead(
        {
            "preferred_state": "Andhra Pradesh",
            "preferred_institution": "",
            "language": "English",
            "annual_budget": "Not decided",
            "concerns": [],
        }
    )


def test_default_not_consented(temporary_database):
    lead_id = make_lead()

    assert not consent.is_eligible_and_consented(lead_id)


def test_explicit_consent_and_eligibility(temporary_database):
    lead_id = make_lead()

    consent.record_experiment_consent(
        lead_id,
        consent_granted=True,
        eligibility_confirmed=True,
    )

    assert consent.is_eligible_and_consented(lead_id)


def test_consent_without_eligibility(temporary_database):
    lead_id = make_lead()

    consent.record_experiment_consent(
        lead_id,
        consent_granted=True,
        eligibility_confirmed=False,
    )

    assert not consent.is_eligible_and_consented(lead_id)


def test_eligibility_without_consent(temporary_database):
    lead_id = make_lead()

    consent.record_experiment_consent(
        lead_id,
        consent_granted=False,
        eligibility_confirmed=True,
    )

    assert not consent.is_eligible_and_consented(lead_id)


def test_consent_revocation(temporary_database):
    lead_id = make_lead()

    consent.record_experiment_consent(lead_id, True, True)
    consent.record_experiment_consent(lead_id, False, True)

    assert not consent.is_eligible_and_consented(lead_id)


def test_unknown_lead_rejected(temporary_database):
    with pytest.raises(ValueError, match="Lead does not exist"):
        consent.record_experiment_consent(
            "unknown",
            True,
            True,
        )


def test_invalid_consent_type_rejected(temporary_database):
    lead_id = make_lead()

    with pytest.raises(ValueError, match="Consent must be a boolean"):
        consent.record_experiment_consent(
            lead_id,
            "yes",
            True,
        )
