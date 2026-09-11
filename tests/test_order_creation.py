from copy import deepcopy
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select, update

from app.auth.tokens import create_access_token
from app.models import MenuItem, Order, OrderItem, Restaurant, User

pytestmark = pytest.mark.integration


@pytest.fixture
def checkout(registration, monkeypatch):
    client, connection = registration
    monkeypatch.setenv("JWT_SECRET", "test-only-order-key-with-at-least-32-characters")
    user_id = connection.scalar(User.__table__.insert().values(
        email=f"{uuid4().hex}@example.com", name="Customer", role="customer", password_hash="unused",
    ).returning(User.id))
    restaurant_id = connection.scalar(Restaurant.__table__.insert().values(name="Kitchen", address="Street").returning(Restaurant.id))
    ids = [connection.scalar(MenuItem.__table__.insert().values(
        restaurant_id=restaurant_id, name=name, price=Decimal(price), available=True,
    ).returning(MenuItem.id)) for name, price in [("Soup", "6.50"), ("Bread", "0.10")]]
    data = {"restaurant_id": restaurant_id, "delivery_name": " Customer ", "delivery_address": " 12 Street ",
            "items": [{"menu_item_id": ids[0], "quantity": 2}, {"menu_item_id": ids[1], "quantity": 3}]}
    headers = {"Authorization": f"Bearer {create_access_token(user_id)}", "Idempotency-Key": uuid4().hex}
    return client, connection, user_id, ids, data, headers


def counts(connection, customer_id):
    return (
        connection.scalar(select(func.count()).select_from(Order).where(Order.customer_id == customer_id)),
        connection.scalar(select(func.count()).select_from(OrderItem).join(Order).where(Order.customer_id == customer_id)),
    )


def test_customer_places_order_with_server_snapshots(checkout):
    client, connection, user_id, ids, data, headers = checkout
    response = client.post("/orders", json=data, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "restaurant_id", "delivery_name", "delivery_address", "status", "total", "currency", "created_at", "items"}
    assert body["status"] == "pending"
    assert body["total"] == "13.30"
    assert body["currency"] == "EUR"
    assert body["delivery_name"] == "Customer"
    assert body["delivery_address"] == "12 Street"
    assert body["items"] == [
        {"menu_item_id": ids[0], "name": "Soup", "unit_price": "6.50", "quantity": 2},
        {"menu_item_id": ids[1], "name": "Bread", "unit_price": "0.10", "quantity": 3},
    ]
    row = connection.execute(select(Order.__table__).where(Order.id == body["id"])).one()
    assert row.customer_id == user_id
    assert row.total == Decimal("13.30")
    assert row.idempotency_key == headers["Idempotency-Key"]
    assert len(row.request_fingerprint) == 64
    assert counts(connection, user_id) == (1, 2)


def test_retry_ignores_menu_changes_and_cart_order(checkout):
    client, connection, user_id, ids, data, headers = checkout
    first = client.post("/orders", json=data, headers=headers)
    connection.execute(update(MenuItem).where(MenuItem.id.in_(ids)).values(name="Changed", price=Decimal("99.00"), available=False))
    data["items"].reverse()
    data["delivery_name"] = "Customer"
    second = client.post("/orders", json=data, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()
    assert counts(connection, user_id) == (1, 2)


@pytest.mark.parametrize("change", ["quantity", "delivery_address", "delivery_name", "restaurant_id", "items"])
def test_key_conflicts_with_different_request(checkout, change):
    client, connection, user_id, _, data, headers = checkout
    assert client.post("/orders", json=data, headers=headers).status_code == 201
    if change == "quantity":
        data["items"][0]["quantity"] += 1
    elif change == "items":
        data["items"].pop()
    elif change == "restaurant_id":
        data[change] += 1
    else:
        data[change] = "Different"
    response = client.post("/orders", json=data, headers=headers)
    assert response.status_code == 409
    assert response.json() == {"detail": "Idempotency key already used for a different request"}
    assert counts(connection, user_id) == (1, 2)


def test_key_scope_and_new_key(checkout):
    client, connection, user_id, _, data, headers = checkout
    first = client.post("/orders", json=data, headers=headers)
    other_id = connection.scalar(User.__table__.insert().values(
        email=f"{uuid4().hex}@example.com", name="Other", role="customer", password_hash="unused",
    ).returning(User.id))
    second = client.post("/orders", json=data, headers={**headers, "Authorization": f"Bearer {create_access_token(other_id)}"})
    third = client.post("/orders", json=data, headers={**headers, "Idempotency-Key": uuid4().hex})
    assert [first.status_code, second.status_code, third.status_code] == [201, 201, 201]
    assert len({r.json()["id"] for r in [first, second, third]}) == 3
    assert counts(connection, user_id) == (2, 4)
    assert counts(connection, other_id) == (1, 2)


@pytest.mark.parametrize("problem,status", [("missing_restaurant", 404), ("missing_item", 422), ("other_restaurant", 422), ("unavailable", 409)])
def test_invalid_cart_leaves_no_order_and_key_can_be_reused(checkout, problem, status):
    client, connection, user_id, ids, data, headers = checkout
    bad = deepcopy(data)
    if problem == "missing_restaurant":
        bad["restaurant_id"] = connection.scalar(select(func.max(Restaurant.id))) + 1
    elif problem == "missing_item":
        bad["items"][1]["menu_item_id"] = connection.scalar(select(func.max(MenuItem.id))) + 1
    elif problem == "other_restaurant":
        bad["restaurant_id"] = connection.scalar(Restaurant.__table__.insert().values(name="Other", address="Street").returning(Restaurant.id))
    else:
        connection.execute(update(MenuItem).where(MenuItem.id == ids[1]).values(available=False))
    assert client.post("/orders", json=bad, headers=headers).status_code == status
    assert counts(connection, user_id) == (0, 0)
    connection.execute(update(MenuItem).where(MenuItem.id == ids[1]).values(available=True))
    assert client.post("/orders", json=data, headers=headers).status_code == 201


@pytest.mark.parametrize("role,status", [("staff", 403), ("admin", 403), ("anonymous", 401), ("bad_token", 401)])
def test_customer_only(checkout, role, status):
    client, connection, user_id, _, data, headers = checkout
    if role == "anonymous":
        headers.pop("Authorization")
    elif role == "bad_token":
        headers["Authorization"] = "Bearer invalid"
    else:
        connection.execute(update(User).where(User.id == user_id).values(role=role))
    assert client.post("/orders", json=data, headers=headers).status_code == status
    assert counts(connection, user_id) == (0, 0)


@pytest.mark.parametrize("key", [None, "", "has space", "x" * 129])
def test_invalid_key(checkout, key):
    client, connection, user_id, _, data, headers = checkout
    if key is None:
        headers.pop("Idempotency-Key")
    else:
        headers["Idempotency-Key"] = key
    assert client.post("/orders", json=data, headers=headers).status_code == 422
    assert counts(connection, user_id) == (0, 0)


@pytest.mark.parametrize("problem", [
    "empty_items", "too_many_items", "duplicate_item", "zero_quantity", "large_quantity", "float_quantity",
    "bool_quantity", "invalid_id", "blank_name", "blank_address", "long_address", "missing_address",
    "total", "currency", "customer_id", "status", "unit_price",
])
def test_invalid_request(checkout, problem):
    client, connection, user_id, _, data, headers = checkout
    if problem == "empty_items":
        data["items"] = []
    elif problem == "too_many_items":
        data["items"] = [{"menu_item_id": i + 1, "quantity": 1} for i in range(101)]
    elif problem == "duplicate_item":
        data["items"].append(data["items"][0].copy())
    elif problem.endswith("quantity"):
        data["items"][0]["quantity"] = {"zero_quantity": 0, "large_quantity": 101, "float_quantity": 1.5, "bool_quantity": True}[problem]
    elif problem == "invalid_id":
        data["items"][0]["menu_item_id"] = 0
    elif problem == "blank_name":
        data["delivery_name"] = " "
    elif problem == "blank_address":
        data["delivery_address"] = " "
    elif problem == "long_address":
        data["delivery_address"] = "x" * 1001
    elif problem == "missing_address":
        del data["delivery_address"]
    elif problem == "unit_price":
        data["items"][0]["unit_price"] = "0.01"
    else:
        data[problem] = "untrusted"
    assert client.post("/orders", json=data, headers=headers).status_code == 422
    assert counts(connection, user_id) == (0, 0)


def test_write_failure_rolls_back_order_and_key(checkout):
    client, connection, user_id, _, data, headers = checkout

    def fail_items(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO order_items"):
            raise RuntimeError("Simulated item write failure")

    event.listen(connection, "before_cursor_execute", fail_items)
    try:
        with pytest.raises(RuntimeError, match="Simulated item write failure"):
            client.post("/orders", json=data, headers=headers)
    finally:
        event.remove(connection, "before_cursor_execute", fail_items)
    assert counts(connection, user_id) == (0, 0)
    assert client.post("/orders", json=data, headers=headers).status_code == 201
