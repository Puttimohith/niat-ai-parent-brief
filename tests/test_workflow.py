import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services import tracking_service
from app.services import ai_service


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    db_path = tmp_path / "test_leads.db"

    monkeypatch.setattr(
        tracking_service,
        "DB_PATH",
        db_path,
    )

    tracking_service.initialize_database()

    yield db_path


@pytest.fixture
def sample_lead():
    return {
        "student_name": "Demo Student",
        "parent_name": "Demo Parent",
        "preferred_state": "Andhra Pradesh",
        "preferred_institution": "Chalapathi University",
        "language": "English",
        "annual_budget": "₹1–2 lakhs",
        "concerns": ["University admission process"],
        "additional_questions": "Is admission guaranteed?",
    }


def test_database_initialization(temporary_database):
    assert temporary_database.exists()

    with sqlite3.connect(temporary_database) as conn:
        result = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='leads'"
        ).fetchone()

    assert result is not None


def test_lead_submission(temporary_database, sample_lead):
    lead_id = tracking_service.save_lead(sample_lead)

    assert lead_id

    metrics = tracking_service.get_dashboard_metrics()

    assert metrics["total_leads"] == 1
    assert metrics["briefs_generated"] == 0
    assert metrics["followups"] == 0


def test_successful_conversion(temporary_database, sample_lead):
    lead_id = tracking_service.save_lead(sample_lead)

    tracking_service.mark_brief_generated(lead_id)
    tracking_service.mark_followup_requested(lead_id)

    metrics = tracking_service.get_dashboard_metrics()

    assert metrics["total_leads"] == 1
    assert metrics["briefs_generated"] == 1
    assert metrics["followups"] == 1
    assert metrics["brief_generation_rate"] == 100
    assert metrics["followup_rate"] == 100


def test_followup_requires_brief(temporary_database, sample_lead):
    lead_id = tracking_service.save_lead(sample_lead)

    tracking_service.mark_followup_requested(lead_id)

    metrics = tracking_service.get_dashboard_metrics()

    assert metrics["followups"] == 0


def test_repeated_updates_do_not_inflate_counts(
    temporary_database, sample_lead
):
    lead_id = tracking_service.save_lead(sample_lead)

    tracking_service.mark_brief_generated(lead_id)
    tracking_service.mark_brief_generated(lead_id)

    tracking_service.mark_followup_requested(lead_id)
    tracking_service.mark_followup_requested(lead_id)

    metrics = tracking_service.get_dashboard_metrics()

    assert metrics["briefs_generated"] == 1
    assert metrics["followups"] == 1


def test_failed_ai_does_not_record_success(
    temporary_database, sample_lead
):
    lead_id = tracking_service.save_lead(sample_lead)

    with patch.object(
        ai_service,
        "generate_parent_brief",
        side_effect=RuntimeError("Simulated AI failure"),
    ):
        with pytest.raises(RuntimeError):
            ai_service.generate_parent_brief(sample_lead)

    metrics = tracking_service.get_dashboard_metrics()

    assert metrics["total_leads"] == 1
    assert metrics["briefs_generated"] == 0
    assert metrics["followups"] == 0


def test_dashboard_language_and_institution(
    temporary_database, sample_lead
):
    tracking_service.save_lead(sample_lead)

    metrics = tracking_service.get_dashboard_metrics()

    assert metrics["languages"][0]["language"] == "English"
    assert metrics["languages"][0]["count"] == 1

    assert (
        metrics["institutions"][0]["preferred_institution"]
        == "Chalapathi University"
    )


def test_database_does_not_store_names(
    temporary_database, sample_lead
):
    tracking_service.save_lead(sample_lead)

    with sqlite3.connect(temporary_database) as conn:
        columns = [
            row[1]
            for row in conn.execute("PRAGMA table_info(leads)")
        ]

    assert "student_name" not in columns
    assert "parent_name" not in columns


def test_demo_and_real_classification(
    temporary_database, sample_lead
):
    demo_id = tracking_service.save_lead(
        sample_lead, record_type="demo"
    )

    real_id = tracking_service.save_lead(
        sample_lead, record_type="real"
    )

    tracking_service.mark_brief_generated(demo_id)
    tracking_service.mark_brief_generated(real_id)
    tracking_service.mark_followup_requested(real_id)

    demo = tracking_service.get_dashboard_metrics("demo")
    real = tracking_service.get_dashboard_metrics("real")
    all_records = tracking_service.get_dashboard_metrics("all")

    assert demo["total_leads"] == 1
    assert demo["briefs_generated"] == 1
    assert demo["followups"] == 0

    assert real["total_leads"] == 1
    assert real["briefs_generated"] == 1
    assert real["followups"] == 1

    assert all_records["total_leads"] == 2
    assert all_records["briefs_generated"] == 2
    assert all_records["followups"] == 1
    assert all_records["followup_rate"] == 50


def test_invalid_record_classification(
    temporary_database, sample_lead
):
    with pytest.raises(ValueError):
        tracking_service.save_lead(
            sample_lead, record_type="invalid"
        )

    assert (
        tracking_service.get_dashboard_metrics("all")[
            "total_leads"
        ] == 0
    )


def test_classification_filter_does_not_mix_languages(
    temporary_database, sample_lead
):
    demo_lead = sample_lead.copy()
    demo_lead["language"] = "English"

    real_lead = sample_lead.copy()
    real_lead["language"] = "Telugu"

    tracking_service.save_lead(
        demo_lead, record_type="demo"
    )

    tracking_service.save_lead(
        real_lead, record_type="real"
    )

    demo = tracking_service.get_dashboard_metrics("demo")
    real = tracking_service.get_dashboard_metrics("real")

    assert len(demo["languages"]) == 1
    assert demo["languages"][0]["language"] == "English"

    assert len(real["languages"]) == 1
    assert real["languages"][0]["language"] == "Telugu"
