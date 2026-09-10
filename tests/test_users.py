from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import User

pytestmark = pytest.mark.integration


@pytest.fixture
def session() -> Generator[Session, None, None]:
    # Every test rolls back its data, including tests that cause SQL errors.
    with Session(get_engine()) as session:
        try:
            yield session
        finally:
            session.rollback()


def user_values() -> dict[str, str]:
    return {
        "email": f"test-{uuid4().hex}@example.com",
        "password_hash": "test-only-placeholder-hash",
        "role": "customer",
        "name": "Test User",
    }


@pytest.mark.parametrize("role", ["customer", "staff", "admin"])
def test_user_round_trip(session: Session, role: str) -> None:
    values = user_values()
    values["role"] = role
    user = User(**values)
    session.add(user)
    session.flush()
    user_id = user.id
    session.expunge_all()

    saved = session.scalars(select(User).where(User.id == user_id)).one()
    assert saved.id > 0
    assert saved.email == values["email"]
    assert saved.password_hash == values["password_hash"]
    assert saved.role == role
    assert saved.name == values["name"]
    assert saved.default_address is None


def test_duplicate_email_is_rejected(session: Session) -> None:
    values = user_values()
    session.execute(insert(User.__table__).values(**values))

    with pytest.raises(IntegrityError) as error:
        session.execute(insert(User.__table__).values(**values))

    assert error.value.orig.diag.constraint_name == "uq_users_email"


def test_invalid_role_is_rejected_by_database(session: Session) -> None:
    values = user_values()
    values["role"] = "owner"

    with pytest.raises(IntegrityError) as error:
        session.execute(insert(User.__table__).values(**values))

    assert error.value.orig.diag.constraint_name == "ck_users_role"


@pytest.mark.parametrize("field", ["email", "password_hash", "role", "name"])
def test_required_field_cannot_be_null(session: Session, field: str) -> None:
    values = {**user_values(), field: None}

    with pytest.raises(IntegrityError) as error:
        session.execute(insert(User.__table__).values(**values))

    assert error.value.orig.sqlstate == "23502"  # PostgreSQL NOT NULL violation.
    assert error.value.orig.diag.column_name == field
