from app.services import tracking_service
from app.services import experiment_event_service


def record_brief_experiment_event(
    lead_id,
    event_type,
    experiment_id="parent_brief_pilot",
):
    """
    Record brief delivery/view only for treatment leads.

    Unassigned leads and control leads are ignored.
    General sharing analytics remain separate.
    """
    if event_type not in (
        "brief_delivered",
        "brief_viewed",
    ):
        raise ValueError("Unsupported brief event")

    with tracking_service.get_connection() as conn:
        try:
            assignment = conn.execute("""
                SELECT group_name
                FROM experiment_assignments
                WHERE experiment_id = ?
                  AND lead_id = ?
            """, (experiment_id, lead_id)).fetchone()
        except Exception as exc:
            if (
                isinstance(exc, tracking_service.sqlite3.OperationalError)
                and "no such table" in str(exc).lower()
            ):
                return False
            raise

    if assignment is None:
        return False

    if assignment["group_name"] != "treatment":
        return False

    experiment_event_service.record_event(
        lead_id,
        event_type,
        experiment_id=experiment_id,
    )

    return True
