"""Deterministically refresh the local prototype database before API startup."""
from __future__ import annotations

import gzip
import os
from pathlib import Path

import psycopg

from app.config import settings


SCHEMAS = (
    "telemetry", "workflow", "recsys", "identity_data", "opportunity",
    "economics", "supply", "catalog",
)


def _database_dsn() -> str:
    return settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _execute_copy_seed(connection: psycopg.Connection, seed_path: Path) -> None:
    """Execute a pg_dump-style SQL file containing COPY FROM STDIN blocks."""
    pending_sql: list[str] = []
    with gzip.open(seed_path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.startswith("COPY "):
                pending_sql.append(line)
                continue

            if pending_sql:
                connection.execute("".join(pending_sql))
                pending_sql.clear()

            copy_statement = line.strip()
            with connection.cursor().copy(copy_statement) as copy:
                for data_line in stream:
                    if data_line.rstrip("\r\n") == r"\.":
                        break
                    copy.write(data_line.encode("utf-8"))

        if pending_sql:
            connection.execute("".join(pending_sql))


def refresh_demo_data() -> None:
    seed_path = Path(os.getenv("DEMO_SEED_PATH", "/demo-seed/001_seed.sql.gz"))
    executive_seed_path = Path(os.getenv("EXECUTIVE_SEED_PATH", "/demo-seed/002_executive_role.sql"))
    if not seed_path.exists():
        raise RuntimeError(f"Demo seed file not found: {seed_path}")

    with psycopg.connect(_database_dsn(), autocommit=True) as connection:
        connection.execute("SELECT pg_advisory_lock(42642026)")
        try:
            schema_list = ", ".join(SCHEMAS)
            connection.execute(f"DROP SCHEMA IF EXISTS {schema_list} CASCADE")
            _execute_copy_seed(connection, seed_path)
            if executive_seed_path.exists():
                connection.execute(executive_seed_path.read_text(encoding="utf-8"))
        finally:
            connection.execute("SELECT pg_advisory_unlock(42642026)")

    print("Deterministic CAT CI demo data refreshed.", flush=True)


if __name__ == "__main__":
    refresh_demo_data()
