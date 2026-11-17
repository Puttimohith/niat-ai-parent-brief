import ast
from pathlib import Path


REQUIRED_LANGUAGES = {
    "English",
    "Telugu",
    "Hindi",
    "Tamil",
    "Kannada",
    "Malayalam",
}


def test_all_six_languages_available():
    source = Path("app/main.py").read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    matching_lists = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.List):
            continue

        values = []

        for element in node.elts:
            if not isinstance(element, ast.Constant):
                break
            if not isinstance(element.value, str):
                break
            values.append(element.value)
        else:
            if REQUIRED_LANGUAGES.issubset(set(values)):
                matching_lists.append(values)

    assert matching_lists, (
        "The application must offer all six languages."
    )


def test_ai_prompt_requires_requested_language():
    source = Path(
        "app/services/ai_service.py"
    ).read_text(encoding="utf-8")

    assert "Write in the requested language" in source
