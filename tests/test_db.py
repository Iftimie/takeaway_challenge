from contextlib import closing

import pytest
from sqlalchemy import text

from app.config import Settings
from app.db import get_session


@pytest.mark.integration
def test_session_connects_to_configured_postgres() -> None:
    settings = Settings()
    with closing(get_session()) as sessions:
        session = next(sessions)
        row = session.execute(
            text("SELECT current_database(), current_user")
        ).one()

    assert row == (settings.postgres_db, settings.postgres_user)
