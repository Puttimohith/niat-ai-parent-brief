from datetime import datetime, timezone

import pytest

from app.services import tracking_service
from app.services import experiment_service
from app.services import experiment_schedule_service as schedule


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        tracking_service,
        "DB_PATH",
        tmp_path / "schedule_test.db",
    )

    experiment_service.create_experiment()


def test_experiment_not_started(temporary_database):
    assert schedule.get_experiment_status() == "not_started"


def test_start_experiment(temporary_database):
    result = schedule.start_experiment()

    assert "started_at" in result
    assert "ended_at" in result
    assert schedule.get_experiment_status() == "active"


def test_experiment_duration(temporary_database):
    result = schedule.start_experiment()

    start = datetime.fromisoformat(result["started_at"])
    end = datetime.fromisoformat(result["ended_at"])

    assert (end - start).days == 14


def test_cannot_start_twice(temporary_database):
    schedule.start_experiment()

    with pytest.raises(
        ValueError,
        match="already started",
    ):
        schedule.start_experiment()


def test_unknown_experiment_rejected(temporary_database):
    with pytest.raises(
        ValueError,
        match="Experiment does not exist",
    ):
        schedule.start_experiment("missing_experiment")
