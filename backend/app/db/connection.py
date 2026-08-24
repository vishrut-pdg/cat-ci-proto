"""Database connection helpers shared by startup utilities."""
from __future__ import annotations

from sqlalchemy.engine import make_url

from app.config import settings


def psycopg_connection_kwargs(database_url: str | None = None) -> dict:
    """Return discrete libpq parameters without reparsing credentials as a DSN.

    Docker Compose treats values in ``.env`` literally. Passing a composed URL
    directly to psycopg breaks when a legacy password contains spaces or URI
    punctuation, while SQLAlchemy's URL parser safely separates each field.
    """
    url = make_url(database_url or settings.database_url)
    return {
        "host": url.host,
        "port": url.port or 5432,
        "dbname": url.database,
        "user": url.username,
        "password": url.password,
    }
