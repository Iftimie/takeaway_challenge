from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.config import Settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        Settings().database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
