from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError

from app.auth.tokens import create_access_token
from app.models import MenuItem, Restaurant, StaffAssignment, User

pytestmark = pytest.mark.integration


@pytest.fixture
def menu(registration, monkeypatch):
    client, connection = registration
    monkeypatch.setenv("JWT_SECRET", "test-only-menu-key-with-at-least-32-characters")
    user_id = connection.scalar(User.__table__.insert().values(
        email=f"{uuid4().hex}@example.com", name="Staff", role="staff",
        password_hash="unused-hash",
    ).returning(User.id))
    restaurant_id = connection.scalar(Restaurant.__table__.insert().values(
        name="Kitchen", address="Street",
    ).returning(Restaurant.id))
    connection.execute(StaffAssignment.__table__.insert().values(
        staff_id=user_id, restaurant_id=restaurant_id,
    ))
    headers = {"Authorization": f"Bearer {create_access_token(user_id)}"}
    return client, connection, user_id, restaurant_id, headers


@pytest.mark.parametrize("price,available", [("12.50", True), ("0.01", False), ("99999999.99", True), (12, True)])
def test_assigned_staff_creates_item(menu, price, available):
    client, connection, _, restaurant_id, headers = menu
    response = client.post(f"/restaurants/{restaurant_id}/menu-items", headers=headers,
                           json={"name": " Soup ", "price": price, "available": available})
    assert response.status_code == 201
    body = response.json()
    assert body == {"id": body["id"], "restaurant_id": restaurant_id, "name": "Soup",
                    "price": format(Decimal(str(price)), ".2f"), "available": available, "currency": "EUR"}
    row = connection.execute(select(MenuItem.__table__).where(MenuItem.id == body["id"])).one()
    assert row.price == Decimal(str(price))
    assert row.name == "Soup"
    assert row.available == available
    assert row.restaurant_id == restaurant_id


def test_availability_defaults_to_true(menu):
    client, _, _, restaurant_id, headers = menu
    response = client.post(f"/restaurants/{restaurant_id}/menu-items", headers=headers,
                           json={"name": "Soup", "price": "5.00"})
    assert response.status_code == 201
    assert response.json()["available"] is True


def test_admin_creates_without_assignment_and_missing_restaurant_is_404(menu):
    client, connection, user_id, restaurant_id, headers = menu
    connection.execute(update(User).where(User.id == user_id).values(role="admin"))
    connection.execute(delete(StaffAssignment).where(StaffAssignment.staff_id == user_id))
    data = {"name": "Admin soup", "price": "5.00"}
    response = client.post(f"/restaurants/{restaurant_id}/menu-items", headers=headers, json=data)
    assert response.status_code == 201
    assert connection.scalar(select(MenuItem.name).where(MenuItem.id == response.json()["id"])) == "Admin soup"
    missing = connection.scalar(select(func.max(Restaurant.id))) + 1
    assert client.post(f"/restaurants/{missing}/menu-items", headers=headers, json=data).status_code == 404


@pytest.mark.parametrize("problem,status", [
    ("anonymous", 401), ("bad_token", 401), ("customer", 403),
    ("removed_assignment", 403), ("other_restaurant", 403), ("missing_restaurant", 404),
])
def test_access_restrictions_create_no_item(menu, problem, status):
    client, connection, user_id, restaurant_id, headers = menu
    if problem == "anonymous":
        headers = {}
    elif problem == "bad_token":
        headers = {"Authorization": "Bearer invalid"}
    elif problem == "customer":
        # The existing token and assignment must not override the current role.
        connection.execute(update(User).where(User.id == user_id).values(role=problem))
    elif problem == "removed_assignment":
        connection.execute(delete(StaffAssignment).where(StaffAssignment.staff_id == user_id))
    elif problem == "other_restaurant":
        restaurant_id = connection.scalar(Restaurant.__table__.insert().values(
            name="Other", address="Street").returning(Restaurant.id))
    elif problem == "missing_restaurant":
        restaurant_id = connection.scalar(select(func.max(Restaurant.id))) + 1
    before = connection.scalar(select(func.count()).select_from(MenuItem))
    response = client.post(f"/restaurants/{restaurant_id}/menu-items", headers=headers,
                           json={"name": "Soup", "price": "5.00"})
    assert response.status_code == status
    assert connection.scalar(select(func.count()).select_from(MenuItem)) == before


@pytest.mark.parametrize("field,value", [
    ("price", "0"), ("price", "-1"), ("price", "1.001"),
    ("price", "100000000.00"), ("price", "NaN"), ("price", "Infinity"),
    ("price", "bad"), ("price", None), ("price", True),
    ("name", " "), ("name", "x" * 201),
    ("available", "false"), ("currency", "USD"), ("restaurant_id", 123),
])
def test_invalid_input_creates_no_item(menu, field, value):
    client, connection, _, restaurant_id, headers = menu
    data = {"name": "Soup", "price": "5.00"}
    data[field] = value
    before = connection.scalar(select(func.count()).select_from(MenuItem))
    assert client.post(f"/restaurants/{restaurant_id}/menu-items", headers=headers, json=data).status_code == 422
    assert connection.scalar(select(func.count()).select_from(MenuItem)) == before


@pytest.mark.parametrize("field", ["name", "price"])
def test_required_fields(menu, field):
    client, _, _, restaurant_id, headers = menu
    data = {"name": "Soup", "price": "5.00"}
    del data[field]
    assert client.post(f"/restaurants/{restaurant_id}/menu-items", headers=headers, json=data).status_code == 422


@pytest.mark.parametrize("restaurant_id", [0, -1, "bad", 99999999999999999999])
def test_invalid_restaurant_id(menu, restaurant_id):
    client, _, _, _, headers = menu
    assert client.post(f"/restaurants/{restaurant_id}/menu-items", headers=headers,
                       json={"name": "Soup", "price": "5.00"}).status_code == 422


@pytest.mark.parametrize("problem", ["zero", "negative", "missing_restaurant", "null_price"])
def test_database_constraints(menu, problem):
    _, connection, _, restaurant_id, _ = menu
    data = {"restaurant_id": restaurant_id, "name": "Soup", "price": Decimal("5.00"), "available": True}
    if problem == "zero":
        data["price"] = Decimal("0")
    elif problem == "negative":
        data["price"] = Decimal("-1")
    elif problem == "null_price":
        data["price"] = None
    else:
        data["restaurant_id"] = connection.scalar(select(func.max(Restaurant.id))) + 1
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(MenuItem.__table__.insert().values(**data))
