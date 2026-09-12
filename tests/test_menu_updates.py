from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, update

from app.auth.tokens import create_access_token
from app.models import MenuItem, Restaurant, StaffAssignment, User

pytestmark = pytest.mark.integration


def test_admin_updates_without_assignment(menu):
    client, connection, user_id, restaurant_id, item_id, headers = menu
    connection.execute(update(User).where(User.id == user_id).values(role="admin"))
    connection.execute(delete(StaffAssignment).where(StaffAssignment.staff_id == user_id))
    response = client.patch(f"/restaurants/{restaurant_id}/menu-items/{item_id}",
                            headers=headers, json={"available": False})
    assert response.status_code == 200
    assert connection.scalar(select(MenuItem.available).where(MenuItem.id == item_id)) is False


@pytest.fixture
def menu(registration, monkeypatch):
    client, connection = registration
    monkeypatch.setenv("JWT_SECRET", "test-only-menu-update-key-at-least-32-characters")
    user_id = connection.scalar(User.__table__.insert().values(
        email=f"{uuid4().hex}@example.com", name="Staff", role="staff",
        password_hash="unused",
    ).returning(User.id))
    restaurant_id = connection.scalar(Restaurant.__table__.insert().values(
        name="Kitchen", address="Street").returning(Restaurant.id))
    connection.execute(StaffAssignment.__table__.insert().values(staff_id=user_id, restaurant_id=restaurant_id))
    item_id = connection.scalar(MenuItem.__table__.insert().values(
        restaurant_id=restaurant_id, name="Soup", price=Decimal("5.00"), available=True,
    ).returning(MenuItem.id))
    headers = {"Authorization": f"Bearer {create_access_token(user_id)}"}
    return client, connection, user_id, restaurant_id, item_id, headers


@pytest.mark.parametrize("changes", [
    {"name": " New soup "}, {"price": "6.25"}, {"available": False},
    {"name": "New soup", "price": "0.01", "available": False},
    {"price": "99999999.99"},
])
def test_partial_update_persists_and_is_public(menu, changes):
    client, connection, _, restaurant_id, item_id, headers = menu
    response = client.patch(f"/restaurants/{restaurant_id}/menu-items/{item_id}", headers=headers, json=changes)
    assert response.status_code == 200
    expected = {"id": item_id, "restaurant_id": restaurant_id, "name": "Soup",
                "price": "5.00", "available": True, "currency": "EUR"}
    expected.update(changes)
    expected["name"] = expected["name"].strip()
    assert response.json() == expected
    row = connection.execute(select(MenuItem.__table__).where(MenuItem.id == item_id)).one()
    assert (row.name, row.price, row.available) == (expected["name"], Decimal(expected["price"]), expected["available"])
    assert client.get(f"/restaurants/{restaurant_id}/menu-items").json() == [expected]


@pytest.mark.parametrize("changes", [
    {}, {"name": None}, {"price": None}, {"available": None},
    {"name": " "}, {"name": "x" * 201}, {"price": "0"}, {"price": "-1"},
    {"price": "1.001"}, {"price": "100000000"}, {"price": "NaN"},
    {"price": "Infinity"}, {"price": True}, {"available": "false"},
    {"restaurant_id": 1}, {"currency": "USD"}, {"id": 1},
    {"name": "Valid change", "price": "-1"},
])
def test_invalid_updates_leave_item_unchanged(menu, changes):
    client, connection, _, restaurant_id, item_id, headers = menu
    statement = select(MenuItem.__table__).where(MenuItem.id == item_id)
    before = connection.execute(statement).one()
    response = client.patch(f"/restaurants/{restaurant_id}/menu-items/{item_id}", headers=headers, json=changes)
    assert response.status_code == 422
    assert connection.execute(statement).one() == before


@pytest.mark.parametrize("problem,status", [
    ("anonymous", 401), ("invalid_token", 401), ("customer", 403),
    ("removed_assignment", 403), ("other_restaurant", 403),
    ("mismatched_item", 404), ("missing_item", 404), ("missing_restaurant", 404),
])
def test_access_and_missing_records(menu, problem, status):
    client, connection, user_id, restaurant_id, item_id, headers = menu
    statement = select(MenuItem.__table__).where(MenuItem.id == item_id)
    before = connection.execute(statement).one()
    if problem == "anonymous":
        headers = {}
    elif problem == "invalid_token":
        headers = {"Authorization": "Bearer invalid"}
    elif problem == "customer":
        connection.execute(update(User).where(User.id == user_id).values(role=problem))
    elif problem == "removed_assignment":
        connection.execute(delete(StaffAssignment).where(StaffAssignment.staff_id == user_id))
    elif problem in ("other_restaurant", "mismatched_item"):
        restaurant_id = connection.scalar(Restaurant.__table__.insert().values(
            name="Other", address="Street").returning(Restaurant.id))
        if problem == "mismatched_item":
            connection.execute(StaffAssignment.__table__.insert().values(staff_id=user_id, restaurant_id=restaurant_id))
    elif problem == "missing_item":
        item_id = connection.scalar(select(func.max(MenuItem.id))) + 1
    elif problem == "missing_restaurant":
        restaurant_id = connection.scalar(select(func.max(Restaurant.id))) + 1
    response = client.patch(f"/restaurants/{restaurant_id}/menu-items/{item_id}", headers=headers,
                            json={"price": "9.50"})
    assert response.status_code == status
    assert connection.execute(statement).one() == before


@pytest.mark.parametrize("item_id", [0, -1, "bad", 99999999999999999])
def test_invalid_item_id(menu, item_id):
    client, _, _, restaurant_id, _, headers = menu
    assert client.patch(f"/restaurants/{restaurant_id}/menu-items/{item_id}", headers=headers,
                        json={"available": False}).status_code == 422
