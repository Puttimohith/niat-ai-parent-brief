"""PostgreSQL sharing backend routing and validation tests."""

import pytest

from app.services import brief_sharing_service as sharing
from app.services import postgres_config
from app.services import postgres_sharing_service as pg


def test_postgres_backend_enabled(monkeypatch):
    monkeypatch.setattr(
        postgres_config,
        "get_database_url",
        lambda: "postgresql://test:test@localhost:6543/postgres",
    )
    assert postgres_config.postgres_enabled() is True


def test_sqlite_backend_when_unconfigured(monkeypatch):
    monkeypatch.setattr(
        postgres_config,
        "get_database_url",
        lambda: "",
    )
    assert postgres_config.postgres_enabled() is False


def test_postgres_create_routing(monkeypatch):
    monkeypatch.setattr(
        postgres_config,
        "postgres_enabled",
        lambda: True,
    )

    def fake_create(*args, **kwargs):
        assert args == ("lead-123", "Demo brief")
        assert kwargs["sharing_consent"] is True
        return "test-token"

    monkeypatch.setattr(
        pg,
        "create_postgres_shared_brief",
        fake_create,
    )

    token = sharing.create_shared_brief(
        "lead-123",
        "Demo brief",
        sharing_consent=True,
    )
    assert token == "test-token"


def test_postgres_retrieve_routing(monkeypatch):
    monkeypatch.setattr(
        postgres_config,
        "postgres_enabled",
        lambda: True,
    )

    monkeypatch.setattr(
        pg,
        "get_postgres_shared_brief",
        lambda token, count_view=False: {
            "lead_id": "lead-123",
            "brief_content": "Persistent demo brief",
            "view_count": 1,
        },
    )

    result = sharing.get_shared_brief(
        "test-token",
        count_view=True,
    )
    assert result["brief_content"] == "Persistent demo brief"


def test_postgres_revoke_routing(monkeypatch):
    monkeypatch.setattr(
        postgres_config,
        "postgres_enabled",
        lambda: True,
    )

    monkeypatch.setattr(
        pg,
        "revoke_postgres_shared_brief",
        lambda lead_id: lead_id == "lead-123",
    )

    assert sharing.revoke_shared_brief("lead-123") is True


def test_postgres_requires_consent():
    with pytest.raises(ValueError, match="sharing consent"):
        pg.create_postgres_shared_brief(
            "lead-123",
            "Demo brief",
            sharing_consent=False,
        )


def test_postgres_rejects_empty_content():
    with pytest.raises(ValueError, match="empty"):
        pg.create_postgres_shared_brief(
            "lead-123",
            "",
            sharing_consent=True,
        )


def test_postgres_rejects_invalid_expiry():
    with pytest.raises(ValueError, match="Expiration"):
        pg.create_postgres_shared_brief(
            "lead-123",
            "Demo brief",
            sharing_consent=True,
            expires_in_days=31,
        )


def test_postgres_rejects_empty_token():
    assert pg.get_postgres_shared_brief("") is None
