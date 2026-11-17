import secrets
from datetime import datetime, timedelta, timezone

from app.services import tracking_service


def initialize_sharing_database():
    tracking_service.initialize_database()

    with tracking_service.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shared_briefs (
                share_token TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL UNIQUE,
                brief_content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                view_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (lead_id)
                    REFERENCES leads(lead_id)
            )
        """)


def create_shared_brief(
    lead_id,
    brief_content,
    sharing_consent=False,
    expires_in_days=7,
):
    if sharing_consent is not True:
        raise ValueError("Explicit sharing consent required")

    if not isinstance(brief_content, str) or not brief_content.strip():
        raise ValueError("Brief content cannot be empty")

    if not isinstance(expires_in_days, int) or isinstance(
        expires_in_days, bool
    ) or not 1 <= expires_in_days <= 30:
        raise ValueError("Expiration must be 1 to 30 days")

    initialize_sharing_database()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=expires_in_days)
    token = secrets.token_urlsafe(32)

    with tracking_service.get_connection() as conn:
        lead = conn.execute("""
            SELECT lead_id, brief_generated
            FROM leads
            WHERE lead_id = ?
        """, (lead_id,)).fetchone()

        if lead is None:
            raise ValueError("Lead does not exist")

        if not lead["brief_generated"]:
            raise ValueError("Brief generation not recorded")

        conn.execute("""
            INSERT INTO shared_briefs (
                share_token,
                lead_id,
                brief_content,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(lead_id) DO UPDATE SET
                share_token = excluded.share_token,
                brief_content = excluded.brief_content,
                created_at = excluded.created_at,
                expires_at = excluded.expires_at,
                view_count = 0
        """, (
            token,
            lead_id,
            brief_content,
            now.isoformat(),
            expires_at.isoformat(),
        ))

    return token


def get_shared_brief(token, count_view=False):
    if not isinstance(token, str) or not token:
        return None

    initialize_sharing_database()

    with tracking_service.get_connection() as conn:
        if count_view:
            conn.execute("BEGIN IMMEDIATE")

        row = conn.execute("""
            SELECT share_token, lead_id, brief_content,
                   expires_at, view_count
            FROM shared_briefs
            WHERE share_token = ?
        """, (token,)).fetchone()

        if row is None:
            return None

        expires_at = datetime.fromisoformat(row["expires_at"])

        if datetime.now(timezone.utc) >= expires_at:
            return None

        if count_view:
            conn.execute("""
                UPDATE shared_briefs
                SET view_count = view_count + 1
                WHERE share_token = ?
            """, (token,))

        return {
            "lead_id": row["lead_id"],
            "brief_content": row["brief_content"],
            "view_count": row["view_count"] + (
                1 if count_view else 0
            ),
        }


def revoke_shared_brief(lead_id):
    initialize_sharing_database()

    with tracking_service.get_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM shared_briefs
            WHERE lead_id = ?
        """, (lead_id,))

    return cursor.rowcount > 0
