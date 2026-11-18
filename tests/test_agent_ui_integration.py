from pathlib import Path


def test_main_imports_agent():
    source = Path("app/main.py").read_text(
        encoding="utf-8"
    )

    assert (
        "from app.services.ai_tool_agent "
        "import ask_niat_agent"
    ) in source


def test_main_calls_agent():
    source = Path("app/main.py").read_text(
        encoding="utf-8"
    )

    assert "ask_niat_agent(" in source
    assert "agent_question.strip()" in source
    assert "language=agent_language" in source


def test_main_displays_tool_evidence():
    source = Path("app/main.py").read_text(
        encoding="utf-8"
    )

    assert 'agent_result["used_public_tool"]' in source
    assert 'agent_result["tool_calls"]' in source
    assert "View actual tool-call evidence" in source


def test_main_supports_regional_languages():
    source = Path("app/main.py").read_text(
        encoding="utf-8"
    )

    for language in (
        "Telugu",
        "Hindi",
        "Tamil",
        "Kannada",
        "Malayalam",
    ):
        assert f'"{language}"' in source
