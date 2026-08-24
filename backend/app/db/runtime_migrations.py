"""Apply idempotent schema/data upgrades to existing database volumes."""
from __future__ import annotations

import os
from pathlib import Path

import psycopg

from app.config import settings


MIGRATION_FILES = (
    "002_executive_role.sql",
    "003_equipment_categories.sql",
)


def _database_dsn() -> str:
    return settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def apply_runtime_migrations() -> None:
    migration_dir = Path(os.getenv("RUNTIME_MIGRATION_DIR", "/demo-seed"))
    paths = [migration_dir / file_name for file_name in MIGRATION_FILES]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise RuntimeError(f"Runtime migration files not found: {', '.join(missing)}")

    with psycopg.connect(_database_dsn(), autocommit=True) as connection:
        connection.execute("SELECT pg_advisory_lock(42642027)")
        try:
            for path in paths:
                connection.execute(path.read_text(encoding="utf-8"))

            if os.getenv("ROLL_DEMO_SNAPSHOTS_ON_START", "false").lower() == "true":
                connection.execute("""
                    WITH latest AS (
                        SELECT MAX(snapshot_at) AS snapshot_at
                        FROM opportunity.metric_snapshots
                    )
                    UPDATE opportunity.metric_snapshots AS snapshot
                    SET snapshot_at = snapshot.snapshot_at
                        + (CURRENT_TIMESTAMP - latest.snapshot_at)
                    FROM latest
                    WHERE latest.snapshot_at IS NOT NULL
                """)
        finally:
            connection.execute("SELECT pg_advisory_unlock(42642027)")

    print("CAT CI runtime database migrations applied.", flush=True)


if __name__ == "__main__":
    apply_runtime_migrations()
