from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.auth.service import password_hasher
from app.models import User

pytestmark = pytest.mark.integration
PASSWORD = "a long test passphrase"


def payload() -> dict[str, str]:
    return {
        "email": f"person.{uuid4().hex}+takeaway@example.com",
        "password": PASSWORD,
        "name": " Test Customer ",
    }


def test_register_stores_customer_and_hash(registration) -> None:
    client, connection = registration
    data = payload()
    data["email"] = f"  {data['email'].upper()}  "
    data["default_address"] = " 12 Test Street "

    response = client.post("/auth/register", json=data)

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "id": body["id"],
        "email": data["email"].strip().lower(),
        "name": "Test Customer",
        "role": "customer",
        "default_address": "12 Test Street",
    }
    row = connection.execute(select(User.__table__).where(User.id == body["id"])).one()
    assert row.email == body["email"]
    assert row.role == "customer"
    assert row.password_hash.startswith("$argon2id$")
    assert row.password_hash != PASSWORD
    assert password_hasher.verify(PASSWORD, row.password_hash)
    assert PASSWORD not in response.text
    assert row.password_hash not in response.text


def test_duplicate_email_returns_conflict_and_session_recovers(registration) -> None:
    client, connection = registration
    data = payload()
    assert client.post("/auth/register", json=data).status_code == 201
    duplicate = client.post("/auth/register", json={**data, "email": data["email"].upper()})

    assert duplicate.status_code == 409
    assert duplicate.json() == {"detail": "Email already registered"}
    assert connection.scalar(
        select(func.count()).select_from(User).where(User.email == data["email"])
    ) == 1
    assert client.post("/auth/register", json=payload()).status_code == 201


def test_existing_mixed_case_email_cannot_be_registered_again(registration) -> None:
    client, connection = registration
    data = payload()
    connection.execute(User.__table__.insert().values(
        email=data["email"].upper(), name="Existing User", role="staff",
        password_hash="test-only-placeholder",
    ))
    assert client.post("/auth/register", json=data).status_code == 409


def test_same_password_gets_distinct_salted_hashes(registration) -> None:
    client, connection = registration
    first = client.post("/auth/register", json=payload())
    second = client.post("/auth/register", json=payload())
    assert first.status_code == second.status_code == 201
    assert first.json()["default_address"] is None
    hashes = connection.execute(select(User.password_hash).where(
        User.id.in_([first.json()["id"], second.json()["id"]])
    )).scalars().all()
    assert len(hashes) == 2
    assert hashes[0] != hashes[1]


@pytest.mark.parametrize("changes", [
    {"email": "not-an-email"},
    {"password": "tiny"},
    {"password": "x" * 129},
    {"password": None},
    {"name": "   "},
    {"name": "x" * 201},
    {"default_address": "  "},
    {"default_address": "x" * 1001},
    {"role": "admin"},
    {"role": "staff"},
    {"role": "customer"},
    {"password_hash": "client-controlled-hash"},
])
def test_invalid_registration_creates_no_user(registration, changes) -> None:
    client, connection = registration
    before = connection.scalar(select(func.count()).select_from(User))
    data = {**payload(), **changes}

    response = client.post("/auth/register", json=data)

    assert response.status_code == 422
    assert connection.scalar(select(func.count()).select_from(User)) == before
    assert all(set(error) == {"loc", "msg", "type"} for error in response.json()["detail"])
    if isinstance(data["password"], str):
        assert data["password"] not in response.text


@pytest.mark.parametrize("field", ["email", "password", "name"])
def test_missing_required_field_is_rejected(registration, field) -> None:
    client, _ = registration
    data = payload()
    del data[field]
    response = client.post("/auth/register", json=data)
    assert response.status_code == 422
    assert PASSWORD not in response.text
