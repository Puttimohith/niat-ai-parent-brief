from pathlib import Path


def test_walkthrough_exists():
    page = Path("app/pages/experiment_walkthrough.py")
    assert page.is_file()


def test_walkthrough_discloses_synthetic_data():
    source = Path(
        "app/pages/experiment_walkthrough.py"
    ).read_text(encoding="utf-8")

    assert "Synthetic demonstration only" in source
    assert "fictional" in source.lower()
    assert "do not write events" in source


def test_walkthrough_includes_both_groups():
    source = Path(
        "app/pages/experiment_walkthrough.py"
    ).read_text(encoding="utf-8")

    assert '"Control", "Treatment"' in source
    assert "eligibility" in source.lower()
    assert "consent" in source.lower()
    assert "next_step_verified" in source
