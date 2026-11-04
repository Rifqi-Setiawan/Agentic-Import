"""Session-wide test database isolation guard.

Enforces strictly isolated test database (imporjaga_test) for all pytest execution.
Guarantees that under no circumstances can tests connect to or mutate operational/production database.
"""
import os
import psycopg
from sqlalchemy import text
from src.core.config import settings
from src.core.database import get_engine

# 1. Force environment and runtime settings to TEST_DATABASE_URL
os.environ["DATABASE_URL"] = settings.TEST_DATABASE_URL
settings.DATABASE_URL = settings.TEST_DATABASE_URL

# 2. Rebind SQLAlchemy engine and SessionLocal to test DB
engine = get_engine()

# 3. Assert current_database() is strictly 'imporjaga_test' via raw psycopg and SQLAlchemy
with psycopg.connect(settings.DATABASE_URL) as conn, conn.cursor() as cur:
    cur.execute("SELECT current_database();")
    active_db = cur.fetchone()[0]
    if active_db != "imporjaga_test":
        raise RuntimeError(
            f"CRITICAL SAFETY FENCE VIOLATION: Test session attempted to connect to '{active_db}'. "
            "Pytest execution is strictly forbidden outside 'imporjaga_test'!"
        )

with engine.connect() as conn:
    result = conn.execute(text("SELECT current_database();")).scalar()
    if result != "imporjaga_test":
        raise RuntimeError(
            f"CRITICAL SAFETY FENCE VIOLATION: SQLAlchemy engine bound to '{result}', expected 'imporjaga_test'!"
        )


def pytest_configure(config):
    """Verify test database guard at pytest session configuration."""
    if settings.DATABASE_URL != settings.TEST_DATABASE_URL:
        raise RuntimeError("CRITICAL SAFETY FENCE VIOLATION: settings.DATABASE_URL != settings.TEST_DATABASE_URL")
    with psycopg.connect(settings.DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT current_database();")
        if cur.fetchone()[0] != "imporjaga_test":
            raise RuntimeError("CRITICAL SAFETY FENCE VIOLATION: current_database is not 'imporjaga_test'")
