import ast
from pathlib import Path

import pytest


MAIN_FILE = Path("app/main.py")


def get_main_ast():
    return ast.parse(
        MAIN_FILE.read_text(encoding="utf-8")
    )


def test_main_has_record_type_configuration():
    tree = get_main_ast()

    source = ast.unparse(tree)

    assert "LEAD_RECORD_TYPE" in source
    assert "demo" in source
    assert "real" in source


def test_save_lead_receives_record_type():
    tree = get_main_ast()

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "save_lead"
    ]

    assert len(calls) == 1

    keywords = {
        keyword.arg: keyword.value
        for keyword in calls[0].keywords
    }

    assert "record_type" in keywords

    assert isinstance(
        keywords["record_type"], ast.Name
    )

    assert keywords["record_type"].id == "record_type"


def resolve_record_type(value):
    record_type = value.strip().lower()

    if record_type not in ("demo", "real"):
        raise ValueError(
            "Invalid LEAD_RECORD_TYPE configuration"
        )

    return record_type


@pytest.mark.parametrize(
    "value, expected",
    [
        ("demo", "demo"),
        ("real", "real"),
        ("DEMO", "demo"),
        ("REAL", "real"),
        (" real ", "real"),
    ],
)
def test_valid_application_modes(value, expected):
    assert resolve_record_type(value) == expected


@pytest.mark.parametrize(
    "value",
    ["invalid", "production", "test", ""],
)
def test_invalid_application_modes(value):
    with pytest.raises(ValueError):
        resolve_record_type(value)


def test_default_application_mode(monkeypatch):
    import os

    monkeypatch.delenv(
        "LEAD_RECORD_TYPE", raising=False
    )

    value = os.getenv(
        "LEAD_RECORD_TYPE", "demo"
    )

    assert resolve_record_type(value) == "demo"
