"""Targeted retrieval from approved public NIAT sources."""

import re
import time

from app.services.public_source_service import (
    fetch_public_source,
)

_CACHE_TTL_SECONDS = 300
_cached_source = None
_cached_at = 0.0


def _get_cached_source():
    """Reuse a recent public-source fetch for up to 5 minutes."""
    global _cached_source, _cached_at

    now = time.monotonic()

    if (
        _cached_source is not None
        and now - _cached_at < _CACHE_TTL_SECONDS
    ):
        return _cached_source

    source = fetch_public_source("niat_knowledge")
    _cached_source = source
    _cached_at = now
    return source


TOPIC_TERMS = {
    "fees": (
        "fee", "fees", "tuition", "scholarship",
        "payment", "refund", "cost", "budget",
    ),
    "admissions": (
        "admission", "eligibility", "nat",
        "enrollment", "university", "degree",
    ),
    "institutions": (
        "university", "institution", "college",
        "campus", "collaboration", "location",
    ),
    "career": (
        "placement", "career", "internship",
        "project", "skill", "employment",
    ),
    "program": (
        "upskilling", "curriculum", "learning",
        "technology", "ai", "program",
    ),
}

MAX_PASSAGES = 5
PASSAGE_CHARS = 550


def _split_passages(content):
    """Split readable text into bounded overlapping passages."""
    words = content.split()

    passages = []
    window_size = 85
    step_size = 65

    for start in range(0, len(words), step_size):
        passage = " ".join(
            words[start:start + window_size]
        )

        if passage:
            passages.append(
                passage[:PASSAGE_CHARS]
            )

    return passages


def _score_passage(passage, terms):
    words = set(
        re.findall(
            r"[a-z0-9]+",
            passage.lower(),
        )
    )

    return sum(
        1 for term in terms
        if term in words
    )


def search_public_sources(topic):
    """Retrieve relevant excerpts with their original source URL."""
    topic = str(topic).strip().lower()

    if topic not in TOPIC_TERMS:
        raise ValueError(
            "Unsupported search topic"
        )

    source = _get_cached_source()

    terms = TOPIC_TERMS[topic]

    candidates = []

    for position, passage in enumerate(
        _split_passages(source["content"])
    ):
        score = _score_passage(
            passage,
            terms,
        )

        if score > 0:
            candidates.append(
                (score, position, passage)
            )

    candidates.sort(
        key=lambda item: (-item[0], item[1])
    )

    selected = candidates[:MAX_PASSAGES]

    return {
        "topic": topic,
        "source_url": source["url"],
        "source_title": source["title"],
        "retrieved_at": source["retrieved_at"],
        "source_truncated": source["truncated"],
        "passages": [
            {
                "text": passage,
                "relevance_score": score,
            }
            for score, _, passage in selected
        ],
    }
