from uuid import uuid4

import pytest
from sqlalchemy import func, select, update

from app.auth.tokens import create_access_token
from app.models import Restaurant, User

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-only-restaurant-key-with-32-characters")


def auth_headers(connection, role="admin"):
    user_id = connection.scalar(User.__table__.insert().values(
        email=f"restaurant-test-{uuid4().hex}@example.com",
        name="Test User", role=role, password_hash="unused-test-hash",
    ).returning(User.id))
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}, user_id


def test_admin_creates_restaurant(registration):
    client, connection = registration
    headers, _ = auth_headers(connection)
    response = client.post("/restaurants", headers=headers, json={
        "name": " Test Kitchen ", "address": " 12 Test Street ",
    })
    assert response.status_code == 201
    body = response.json()
    assert body == {"id": body["id"], "name": "Test Kitchen", "address": "12 Test Street"}
    assert body["id"] > 0
    row = connection.execute(select(Restaurant.__table__).where(Restaurant.id == body["id"])).one()
    assert row.name == body["name"]
    assert row.address == body["address"]


@pytest.mark.parametrize("role", ["customer", "staff"])
def test_non_admin_cannot_create_restaurant(registration, role):
    client, connection = registration
    headers, _ = auth_headers(connection, role)
    before = connection.scalar(select(func.count()).select_from(Restaurant))
    response = client.post("/restaurants", headers=headers, json={"name": "Kitchen", "address": "Street"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}
    assert connection.scalar(select(func.count()).select_from(Restaurant)) == before


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer invalid-token"}])
def test_unauthenticated_cannot_create_restaurant(registration, headers):
    client, connection = registration
    before = connection.scalar(select(func.count()).select_from(Restaurant))
    response = client.post("/restaurants", headers=headers, json={"name": "Kitchen", "address": "Street"})
    assert response.status_code == 401
    assert connection.scalar(select(func.count()).select_from(Restaurant)) == before


def test_admin_permission_uses_current_database_role(registration):
    client, connection = registration
    headers, user_id = auth_headers(connection)
    connection.execute(update(User).where(User.id == user_id).values(role="customer"))
    response = client.post("/restaurants", headers=headers, json={"name": "Kitchen", "address": "Street"})
    assert response.status_code == 403


@pytest.mark.parametrize("data", [
    {}, {"name": "Kitchen"}, {"address": "Street"},
    {"name": "  ", "address": "Street"},
    {"name": "Kitchen", "address": "  "},
    {"name": "x" * 201, "address": "Street"},
    {"name": "Kitchen", "address": "x" * 1001},
    {"name": "Kitchen", "address": "Street", "id": 123},
])
def test_invalid_restaurant_creates_no_row(registration, data):
    client, connection = registration
    headers, _ = auth_headers(connection)
    before = connection.scalar(select(func.count()).select_from(Restaurant))
    assert client.post("/restaurants", headers=headers, json=data).status_code == 422
    assert connection.scalar(select(func.count()).select_from(Restaurant)) == before
