from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, text

from app.db.config import Settings


def create_mysql_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.mysql_pool_size,
        pool_timeout=settings.mysql_pool_timeout_seconds,
        connect_args={"connect_timeout": settings.mysql_connect_timeout_seconds},
    )


@contextmanager
def read_only_connection(engine: Engine) -> Iterator[object]:
    with engine.connect() as connection:
        connection.execute(text("SET SESSION TRANSACTION READ ONLY"))
        yield connection


def check_connection(engine: Engine) -> tuple[str, str]:
    with read_only_connection(engine) as connection:
        row = connection.execute(text("SELECT DATABASE(), VERSION()")).one()
        return str(row[0]), str(row[1])
