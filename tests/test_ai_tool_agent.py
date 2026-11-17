"""Regression tests for Gemini tool-call recovery."""

from types import SimpleNamespace

import pytest

from app.services import ai_tool_agent


def fake_source_search(topic):
    return {
        "topic": topic,
        "source_url": (
            "https://www.niatindia.com/llm-info"
        ),
        "retrieved_at": (
            "2026-11-17T00:00:00+00:00"
        ),
        "source_truncated": True,
        "passages": [
            {
                "text": (
                    "NIAT is an upskilling initiative. "
                    "University admission is separate."
                ),
                "relevance_score": 2,
            }
        ],
    }


def test_recovery_receives_actual_source_passages(
    monkeypatch,
):
    captured = {}

    class FakeChat:
        def send_message(self, message):
            # Simulate Gemini executing the Python tool
            # but returning no final text.
            self.tool("admissions")
            return SimpleNamespace(text=None)

    class FakeChats:
        def create(self, model, config):
            chat = FakeChat()
            chat.tool = config.tools[0]
            return chat

    class FakeModels:
        def generate_content(
            self, model, contents, config
        ):
            captured["recovery_prompt"] = contents
            return SimpleNamespace(
                text=(
                    "NIAT enrollment and university "
                    "admission are separate."
                )
            )

    class FakeClient:
        def __init__(self, **kwargs):
            self.chats = FakeChats()
            self.models = FakeModels()

        def close(self):
            pass

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "fake-test-key",
    )

    monkeypatch.setattr(
        ai_tool_agent.genai,
        "Client",
        FakeClient,
    )

    monkeypatch.setattr(
        ai_tool_agent,
        "search_public_sources",
        fake_source_search,
    )

    result = ai_tool_agent.ask_niat_agent(
        "Explain NIAT admissions.",
    )

    assert result["used_public_tool"]
    assert len(result["tool_calls"]) == 1

    prompt = captured["recovery_prompt"]

    assert "NIAT is an upskilling initiative" in prompt
    assert "University admission is separate" in prompt
    assert "niatindia.com/llm-info" in prompt


def test_empty_response_without_tool_fails(
    monkeypatch,
):
    class FakeChat:
        def send_message(self, message):
            return SimpleNamespace(text=None)

    class FakeChats:
        def create(self, model, config):
            return FakeChat()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chats = FakeChats()

        def close(self):
            pass

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "fake-test-key",
    )

    monkeypatch.setattr(
        ai_tool_agent.genai,
        "Client",
        FakeClient,
    )

    with pytest.raises(
        RuntimeError,
        match="without executing",
    ):
        ai_tool_agent.ask_niat_agent(
            "Explain NIAT admissions."
        )


def test_unsupported_language_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "fake-test-key",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported language",
    ):
        ai_tool_agent.ask_niat_agent(
            "Explain NIAT.",
            language="Unsupported",
        )
