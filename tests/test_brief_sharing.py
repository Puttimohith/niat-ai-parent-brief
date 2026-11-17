import pytest

from app.services import tracking_service
from app.services import brief_sharing_service as sharing


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        tracking_service,
        "DB_PATH",
        tmp_path / "sharing_test.db",
    )


def generated_lead():
    lead_id = tracking_service.save_lead({
        "preferred_state": "Andhra Pradesh",
        "preferred_institution": "Demo Institution",
        "language": "English",
        "annual_budget": "Not decided",
        "concerns": [],
    })

    tracking_service.mark_brief_generated(lead_id)
    return lead_id


def test_sharing_requires_explicit_consent(temporary_database):
    lead_id = generated_lead()

    with pytest.raises(ValueError, match="sharing consent"):
        sharing.create_shared_brief(
            lead_id,
            "Demo brief",
        )


def test_create_and_retrieve(temporary_database):
    lead_id = generated_lead()

    token = sharing.create_shared_brief(
        lead_id,
        "Demo decision brief",
        sharing_consent=True,
    )

    assert len(token) >= 32

    result = sharing.get_shared_brief(token)

    assert result["brief_content"] == "Demo decision brief"


def test_unknown_token(temporary_database):
    assert sharing.get_shared_brief("invalid-token") is None


def test_view_count(temporary_database):
    lead_id = generated_lead()

    token = sharing.create_shared_brief(
        lead_id,
        "Demo brief",
        sharing_consent=True,
    )

    sharing.get_shared_brief(token, count_view=True)
    sharing.get_shared_brief(token, count_view=True)

    result = sharing.get_shared_brief(token)

    assert result["view_count"] == 2


def test_revoke(temporary_database):
    lead_id = generated_lead()

    token = sharing.create_shared_brief(
        lead_id,
        "Demo brief",
        sharing_consent=True,
    )

    assert sharing.revoke_shared_brief(lead_id) is True
    assert sharing.get_shared_brief(token) is None


def test_old_token_invalidated_on_replacement(temporary_database):
    lead_id = generated_lead()

    first = sharing.create_shared_brief(
        lead_id, "First brief", sharing_consent=True
    )

    second = sharing.create_shared_brief(
        lead_id, "Updated brief", sharing_consent=True
    )

    assert first != second
    assert sharing.get_shared_brief(first) is None
    assert sharing.get_shared_brief(second) is not None


def test_unrecorded_generation_rejected(temporary_database):
    lead_id = tracking_service.save_lead({
        "preferred_state": "Telangana",
        "concerns": [],
    })

    with pytest.raises(ValueError, match="generation not recorded"):
        sharing.create_shared_brief(
            lead_id,
            "Demo brief",
            sharing_consent=True,
        )
