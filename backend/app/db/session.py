from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

from app.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)


def get_db() -> Generator[Connection, None, None]:
    with engine.connect() as connection:
        yield connection