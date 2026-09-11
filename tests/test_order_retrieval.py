from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select, update

from app.auth.tokens import create_access_token
from app.models import MenuItem, Order, OrderItem, Restaurant, User

pytestmark = pytest.mark.integration


@pytest.fixture
def history(registration, monkeypatch):
    client, connection = registration
    monkeypatch.setenv("JWT_SECRET", "test-only-history-key-at-least-32-characters")
    customers = [connection.scalar(User.__table__.insert().values(
        email=f"{uuid4().hex}@example.com", name="Customer", role="customer", password_hash="unused",
    ).returning(User.id)) for _ in range(2)]
    restaurant_id = connection.scalar(Restaurant.__table__.insert().values(name="Kitchen", address="Street").returning(Restaurant.id))
    menu_id = connection.scalar(MenuItem.__table__.insert().values(
        restaurant_id=restaurant_id, name="Soup", price=Decimal("6.50"), available=True,
    ).returning(MenuItem.id))

    def add_order(customer_id=customers[0]):
        order_id = connection.scalar(Order.__table__.insert().values(
            customer_id=customer_id, restaurant_id=restaurant_id, delivery_name="Customer",
            delivery_address="Private address", status="pending", total=Decimal("13.00"), currency="EUR",
            idempotency_key=uuid4().hex, request_fingerprint="a" * 64,
        ).returning(Order.id))
        connection.execute(OrderItem.__table__.insert().values(
            order_id=order_id, menu_item_id=menu_id, name="Soup", unit_price=Decimal("6.50"), quantity=2,
        ))
        return order_id

    headers = {"Authorization": f"Bearer {create_access_token(customers[0])}"}
    return client, connection, customers, menu_id, headers, add_order


def test_detail_uses_snapshots_and_current_status(history):
    client, connection, _, menu_id, headers, add_order = history
    order_id = add_order()
    connection.execute(update(MenuItem).where(MenuItem.id == menu_id).values(name="Changed", price=Decimal("9.00")))
    connection.execute(update(Order).where(Order.id == order_id).values(status="accepted"))
    response = client.get(f"/orders/{order_id}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "restaurant_id", "delivery_name", "delivery_address", "status", "total", "currency", "created_at", "items"}
    assert body["id"] == order_id
    assert body["delivery_address"] == "Private address"
    assert body["status"] == "accepted"
    assert body["total"] == "13.00" and body["currency"] == "EUR"
    assert body["items"] == [{"menu_item_id": menu_id, "name": "Soup", "unit_price": "6.50", "quantity": 2}]


def test_list_is_scoped_and_paginated_newest_first(history):
    client, _, customers, _, headers, add_order = history
    ids = []
    for _ in range(23):
        ids.append(add_order())
        add_order(customers[1])
    first = client.get("/orders", headers=headers)
    second = client.get("/orders?limit=20&offset=20", headers=headers)
    assert first.status_code == second.status_code == 200
    expected = list(reversed(ids))
    assert [row["id"] for row in first.json()] == expected[:20]
    assert [row["id"] for row in second.json()] == expected[20:]
    assert set(first.json()[0]) == {"id", "restaurant_id", "status", "total", "currency", "created_at"}
    assert first.json()[0]["total"] == "13.00"


def test_maximum_page_size(history):
    client, _, _, _, headers, add_order = history
    ids = [add_order() for _ in range(101)]
    response = client.get("/orders?limit=100", headers=headers)
    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == list(reversed(ids))[:100]


def test_empty_history_and_page(history):
    client, _, customers, _, headers, add_order = history
    add_order(customers[1])
    response = client.get("/orders", headers=headers)
    assert response.status_code == 200 and response.json() == []
    add_order()
    response = client.get("/orders?offset=10000", headers=headers)
    assert response.status_code == 200 and response.json() == []


def test_other_customer_order_indistinguishable_from_missing(history):
    client, connection, customers, _, headers, add_order = history
    other_id = add_order(customers[1])
    missing_id = connection.scalar(select(func.max(Order.id))) + 1
    for order_id in [other_id, missing_id]:
        response = client.get(f"/orders/{order_id}", headers=headers)
        assert response.status_code == 404
        assert response.json() == {"detail": "Order not found"}


@pytest.mark.parametrize("endpoint", ["list", "detail"])
@pytest.mark.parametrize("role,status", [("anonymous", 401), ("invalid", 401), ("staff", 403), ("admin", 403)])
def test_customer_access_required(history, endpoint, role, status):
    client, connection, customers, _, headers, add_order = history
    order_id = add_order()
    if role == "anonymous":
        headers = {}
    elif role == "invalid":
        headers = {"Authorization": "Bearer invalid"}
    else:
        # The token predates this role change: the database role must be used.
        connection.execute(update(User).where(User.id == customers[0]).values(role=role))
    response = client.get("/orders" if endpoint == "list" else f"/orders/{order_id}", headers=headers)
    assert response.status_code == status


@pytest.mark.parametrize("query", ["limit=0", "limit=-1", "limit=101", "limit=bad", "offset=-1", "offset=10001", "offset=bad"])
def test_invalid_pagination(history, query):
    client, _, _, _, headers, _ = history
    assert client.get(f"/orders?{query}", headers=headers).status_code == 422


@pytest.mark.parametrize("order_id", [0, -1, "bad", 999999999999999999])
def test_invalid_order_id(history, order_id):
    client, _, _, _, headers, _ = history
    assert client.get(f"/orders/{order_id}", headers=headers).status_code == 422
