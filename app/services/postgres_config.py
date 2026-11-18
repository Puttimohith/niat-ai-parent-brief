"""Server-side PostgreSQL configuration for persistent shared briefs."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_database_url():
    """Read PostgreSQL URL without logging or exposing credentials."""
    url = os.getenv("DATABASE_URL", "").strip()

    if url:
        return url

    try:
        import streamlit as st
        url = str(st.secrets.get("DATABASE_URL", "")).strip()
        return url
    except (FileNotFoundError, KeyError):
        return ""


def postgres_enabled():
    return bool(get_database_url())


def get_postgres_connection():
    """Open a short-lived PostgreSQL connection."""
    import psycopg

    url = get_database_url()

    if not url:
        raise RuntimeError("DATABASE_URL is not configured")

    return psycopg.connect(
        url,
        sslmode="require",
        connect_timeout=15,
        prepare_threshold=None,
    )
