import pytest

from app.services import source_search_service as service


def fake_source():
    return {
        "url": "https://www.niatindia.com/llm-info",
        "title": "NIAT Public Knowledge",
        "retrieved_at": "2026-11-17T00:00:00+00:00",
        "truncated": False,
        "content": (
            "NIAT provides an upskilling program. "
            "University degree admission is separate. "
            "Scholarship and fees must be confirmed. "
            "Career projects support practical learning. "
        ) * 20,
    }


def test_search_returns_source_metadata(monkeypatch):
    monkeypatch.setattr(
        service,
        "fetch_public_source",
        lambda source_id: fake_source(),
    )

    result = service.search_public_sources(
        "admissions"
    )

    assert result["topic"] == "admissions"
    assert result["source_url"].startswith(
        "https://www.niatindia.com/"
    )
    assert result["passages"]


def test_fee_search_returns_relevant_passages(monkeypatch):
    monkeypatch.setattr(
        service,
        "fetch_public_source",
        lambda source_id: fake_source(),
    )

    result = service.search_public_sources(
        "fees"
    )

    assert any(
        "fees" in passage["text"].lower()
        for passage in result["passages"]
    )


def test_unknown_topic_rejected():
    with pytest.raises(ValueError):
        service.search_public_sources(
            "unapproved"
        )


def test_passage_count_is_bounded(monkeypatch):
    monkeypatch.setattr(
        service,
        "fetch_public_source",
        lambda source_id: fake_source(),
    )

    result = service.search_public_sources(
        "program"
    )

    assert len(result["passages"]) <= 5


def test_passage_length_is_bounded():
    content = "upskilling " * 1000

    passages = service._split_passages(content)

    assert passages
    assert all(
        len(passage) <= 550
        for passage in passages
    )
