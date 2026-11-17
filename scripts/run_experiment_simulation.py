import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services import tracking_service
from app.services import experiment_service
from app.services import experiment_consent_service
from app.services import experiment_schedule_service
from app.services import experiment_event_service
from app.services import experiment_metrics_service


def simulate(control_conversions, treatment_conversions):
    if not all(
        isinstance(value, int) and 0 <= value <= 100
        for value in (control_conversions, treatment_conversions)
    ):
        raise ValueError("Conversions must be integers from 0 to 100")

    with tempfile.TemporaryDirectory() as directory:
        tracking_service.DB_PATH = (
            Path(directory) / "synthetic_experiment.db"
        )

        experiment_service.create_experiment(
            duration_days=14,
            target_per_group=100,
        )
        experiment_schedule_service.start_experiment()

        groups = {"control": [], "treatment": []}

        for _ in range(200):
            lead_id = tracking_service.save_lead(
                {
                    "preferred_state": "Andhra Pradesh",
                    "preferred_institution": "Fictional Institution",
                    "language": "English",
                    "annual_budget": "Not specified",
                    "concerns": ["Fees"],
                },
                record_type="demo",
            )

            experiment_consent_service.record_experiment_consent(
                lead_id,
                consent_granted=True,
                eligibility_confirmed=True,
            )

            group = experiment_service.assign_lead(lead_id)
            groups[group].append(lead_id)

        for group, total in (
            ("control", control_conversions),
            ("treatment", treatment_conversions),
        ):
            for lead_id in groups[group][:total]:
                experiment_event_service.record_event(
                    lead_id,
                    "next_step_verified",
                    verified_by="synthetic_simulator",
                )

        metrics = experiment_metrics_service.get_experiment_metrics(
            record_type="demo",
            as_of=datetime.now(timezone.utc) + timedelta(days=8),
        )

        assert len(groups["control"]) == 100
        assert len(groups["treatment"]) == 100

        return metrics


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python -m scripts.run_experiment_simulation "
            "<control> <treatment>"
        )

    result = simulate(int(sys.argv[1]), int(sys.argv[2]))
    print(json.dumps(result))
