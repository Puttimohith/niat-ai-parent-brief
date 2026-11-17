from datetime import datetime, timedelta, timezone

from app.services import experiment_event_service
from app.services import tracking_service


def get_experiment_metrics(
    experiment_id="parent_brief_pilot",
    record_type="demo",
    as_of=None,
):
    if record_type not in ("demo", "real"):
        raise ValueError("Invalid record type")

    experiment_event_service.initialize_event_database()

    if as_of is None:
        as_of = datetime.now(timezone.utc)

    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")

    as_of = as_of.astimezone(timezone.utc)

    with tracking_service.get_connection() as conn:
        assignments = conn.execute("""
            SELECT a.lead_id, a.group_name, a.assigned_at
            FROM experiment_assignments a
            JOIN leads l ON l.lead_id = a.lead_id
            WHERE a.experiment_id = ?
              AND l.record_type = ?
        """, (experiment_id, record_type)).fetchall()

        events = conn.execute("""
            SELECT lead_id, event_type, event_time
            FROM experiment_events
            WHERE experiment_id = ?
        """, (experiment_id,)).fetchall()

    events_by_lead = {}

    for event in events:
        events_by_lead.setdefault(
            event["lead_id"], []
        ).append(event)

    result = {
        "control": {
            "assigned": 0,
            "verified_conversions": 0,
            "conversion_rate": 0.0,
            "matured_leads": 0,
            "matured_conversion_rate": 0.0,
        },
        "treatment": {
            "assigned": 0,
            "verified_conversions": 0,
            "conversion_rate": 0.0,
            "matured_leads": 0,
            "matured_conversion_rate": 0.0,
        },
    }

    matured_conversions = {
        "control": 0,
        "treatment": 0,
    }

    for assignment in assignments:
        group = assignment["group_name"]
        lead_id = assignment["lead_id"]

        assigned_at = datetime.fromisoformat(
            assignment["assigned_at"]
        )

        deadline = assigned_at + timedelta(days=7)

        result[group]["assigned"] += 1

        matured = as_of >= deadline

        if matured:
            result[group]["matured_leads"] += 1

        converted = False

        for event in events_by_lead.get(lead_id, []):
            if event["event_type"] != "next_step_verified":
                continue

            event_time = datetime.fromisoformat(
                event["event_time"]
            )

            if (
                assigned_at <= event_time <= deadline
                and event_time <= as_of
            ):
                converted = True
                break

        if converted:
            result[group]["verified_conversions"] += 1

            if matured:
                matured_conversions[group] += 1

    for group in ("control", "treatment"):
        assigned = result[group]["assigned"]
        converted = result[group]["verified_conversions"]
        matured = result[group]["matured_leads"]

        if assigned:
            result[group]["conversion_rate"] = round(
                converted / assigned * 100,
                2,
            )

        if matured:
            result[group]["matured_conversion_rate"] = round(
                matured_conversions[group] / matured * 100,
                2,
            )

    result["uplift_percentage_points"] = round(
        result["treatment"]["conversion_rate"]
        - result["control"]["conversion_rate"],
        2,
    )

    result["matured_uplift_percentage_points"] = round(
        result["treatment"]["matured_conversion_rate"]
        - result["control"]["matured_conversion_rate"],
        2,
    )

    return result
