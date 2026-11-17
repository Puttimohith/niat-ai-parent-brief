import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "leads.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection



def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                preferred_state TEXT NOT NULL,
                preferred_institution TEXT,
                language TEXT,
                annual_budget TEXT,
                concerns TEXT,
                created_at TEXT NOT NULL,
                brief_generated INTEGER DEFAULT 0,
                followup_requested INTEGER DEFAULT 0,
                record_type TEXT NOT NULL DEFAULT 'demo'
                    CHECK (record_type IN ('demo', 'real'))
            )
        """)

        columns = [
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(leads)"
            )
        ]

        if "record_type" not in columns:
            conn.execute("""
                ALTER TABLE leads
                ADD COLUMN record_type TEXT NOT NULL
                DEFAULT 'demo'
                CHECK (record_type IN ('demo', 'real'))
            """)

def save_lead(lead_data, record_type="demo"):
    initialize_database()

    if record_type not in ("demo", "real"):
        raise ValueError("Invalid record type")

    lead_id = str(uuid4())

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO leads (
                lead_id, preferred_state,
                preferred_institution, language,
                annual_budget, concerns, created_at,
                record_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_id,
            lead_data.get("preferred_state", ""),
            lead_data.get("preferred_institution", ""),
            lead_data.get("language", "English"),
            lead_data.get("annual_budget", ""),
            json.dumps(lead_data.get("concerns", [])),
            datetime.now(timezone.utc).isoformat(),
            record_type,
        ))

    return lead_id


def mark_brief_generated(lead_id):
    initialize_database()
    with get_connection() as conn:
        conn.execute("""
            UPDATE leads
            SET brief_generated = 1
            WHERE lead_id = ?
        """, (lead_id,))


def mark_followup_requested(lead_id):
    initialize_database()
    with get_connection() as conn:
        conn.execute("""
            UPDATE leads
            SET followup_requested = 1
            WHERE lead_id = ? AND brief_generated = 1
        """, (lead_id,))



def get_dashboard_metrics(record_type="all"):
    initialize_database()

    if record_type not in ("all", "demo", "real"):
        raise ValueError("Invalid record type")

    where_clause = (
        "" if record_type == "all"
        else "WHERE record_type = ?"
    )

    params = (
        () if record_type == "all"
        else (record_type,)
    )

    with get_connection() as conn:
        totals = conn.execute(f"""
            SELECT
                COUNT(*) AS total_leads,
                COALESCE(SUM(brief_generated), 0)
                    AS briefs_generated,
                COALESCE(SUM(followup_requested), 0)
                    AS followups
            FROM leads
            {where_clause}
        """, params).fetchone()

        languages = conn.execute(f"""
            SELECT language, COUNT(*) AS count
            FROM leads
            {where_clause}
            GROUP BY language
            ORDER BY count DESC
        """, params).fetchall()

        institution_filter = (
            "WHERE TRIM(preferred_institution) != ''"
            if record_type == "all"
            else """
            WHERE TRIM(preferred_institution) != ''
            AND record_type = ?
            """
        )

        institutions = conn.execute(f"""
            SELECT preferred_institution, COUNT(*) AS count
            FROM leads
            {institution_filter}
            GROUP BY preferred_institution
            ORDER BY count DESC
        """, params).fetchall()

    total = totals["total_leads"]
    briefs = totals["briefs_generated"]
    followups = totals["followups"]

    return {
        "total_leads": total,
        "briefs_generated": briefs,
        "followups": followups,
        "brief_generation_rate": round(
            briefs / total * 100, 2
        ) if total else 0,
        "followup_rate": round(
            followups / briefs * 100, 2
        ) if briefs else 0,
        "languages": [dict(row) for row in languages],
        "institutions": [dict(row) for row in institutions],
    }
