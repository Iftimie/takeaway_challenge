from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection
from sqlalchemy.orm import Session

from app.db import get_engine, get_session
from app.main import app


@pytest.fixture
def registration() -> Generator[tuple[TestClient, Connection], None, None]:
    # Route commits release savepoints; the outer transaction still rolls back
    # everything this test creates. Each request gets its own session.
    with get_engine().connect() as connection:
        transaction = connection.begin()

        def session_override() -> Generator[Session, None, None]:
            with Session(connection, join_transaction_mode="create_savepoint") as session:
                yield session

        app.dependency_overrides[get_session] = session_override
        try:
            with TestClient(app) as client:
                yield client, connection
        finally:
            app.dependency_overrides.pop(get_session, None)
            transaction.rollback()
