"""Persistent PostgreSQL storage for consented shared briefs."""

import secrets
from datetime import datetime, timedelta, timezone

from psycopg.rows import dict_row

from app.services.postgres_config import get_postgres_connection
from app.services import tracking_service


def initialize_postgres_sharing():
    with get_postgres_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS shared_briefs (
                    share_token TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL UNIQUE,
                    brief_content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    view_count INTEGER NOT NULL DEFAULT 0
                )
            """)


def create_postgres_shared_brief(
    lead_id,
    brief_content,
    sharing_consent=False,
    expires_in_days=7,
):
    if sharing_consent is not True:
        raise ValueError("Explicit sharing consent required")

    if not isinstance(brief_content, str) or not brief_content.strip():
        raise ValueError("Brief content cannot be empty")

    if (
        not isinstance(expires_in_days, int)
        or isinstance(expires_in_days, bool)
        or not 1 <= expires_in_days <= 30
    ):
        raise ValueError("Expiration must be 1 to 30 days")

    tracking_service.initialize_database()

    with tracking_service.get_connection() as conn:
        lead = conn.execute(
            """
            SELECT lead_id, brief_generated
            FROM leads
            WHERE lead_id = ?
            """,
            (lead_id,),
        ).fetchone()

    if lead is None:
        raise ValueError("Lead does not exist")

    if not lead["brief_generated"]:
        raise ValueError("Brief generation not recorded")

    initialize_postgres_sharing()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=expires_in_days)
    token = secrets.token_urlsafe(32)

    with get_postgres_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO shared_briefs (
                    share_token,
                    lead_id,
                    brief_content,
                    created_at,
                    expires_at
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (lead_id) DO UPDATE SET
                    share_token = EXCLUDED.share_token,
                    brief_content = EXCLUDED.brief_content,
                    created_at = EXCLUDED.created_at,
                    expires_at = EXCLUDED.expires_at,
                    view_count = 0
                """,
                (token, lead_id, brief_content, now, expires_at),
            )

    return token


def get_postgres_shared_brief(token, count_view=False):
    if not isinstance(token, str) or not token:
        return None

    initialize_postgres_sharing()

    with get_postgres_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if count_view:
                cur.execute(
                    """
                    UPDATE shared_briefs
                    SET view_count = view_count + 1
                    WHERE share_token = %s
                      AND expires_at > NOW()
                    RETURNING lead_id, brief_content, view_count
                    """,
                    (token,),
                )
            else:
                cur.execute(
                    """
                    SELECT lead_id, brief_content, view_count
                    FROM shared_briefs
                    WHERE share_token = %s
                      AND expires_at > NOW()
                    """,
                    (token,),
                )

            row = cur.fetchone()

    return dict(row) if row else None


def revoke_postgres_shared_brief(lead_id):
    initialize_postgres_sharing()

    with get_postgres_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM shared_briefs WHERE lead_id = %s",
                (lead_id,),
            )
            return cur.rowcount > 0
