from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, update

from app.auth.tokens import create_access_token
from app.models import MenuItem, Order, OrderItem, Restaurant, StaffAssignment, User

pytestmark = pytest.mark.integration


@pytest.fixture
def kitchen(registration, monkeypatch):
    client, connection = registration
    monkeypatch.setenv("JWT_SECRET", "staff-orders-test-key-at-least-32-characters")
    users = [connection.scalar(User.__table__.insert().values(
        email=f"{uuid4().hex}@example.com", name="Test", role=role, password_hash="unused",
    ).returning(User.id)) for role in ["staff", "customer", "customer"]]
    restaurants = [connection.scalar(Restaurant.__table__.insert().values(name="Kitchen", address="Street").returning(Restaurant.id)) for _ in range(2)]
    menu_ids = [connection.scalar(MenuItem.__table__.insert().values(
        restaurant_id=restaurant_id, name="Soup", price=Decimal("6.50"), available=True,
    ).returning(MenuItem.id)) for restaurant_id in restaurants]
    connection.execute(StaffAssignment.__table__.insert().values(staff_id=users[0], restaurant_id=restaurants[0]))

    def add_order(restaurant=0, customer=1):
        order_id = connection.scalar(Order.__table__.insert().values(
            customer_id=users[customer], restaurant_id=restaurants[restaurant], delivery_name=f"Customer {customer}",
            delivery_address=f"Address {customer}", status="pending", total=Decimal("13.00"), currency="EUR",
            idempotency_key=uuid4().hex, request_fingerprint="a" * 64,
        ).returning(Order.id))
        connection.execute(OrderItem.__table__.insert().values(
            order_id=order_id, menu_item_id=menu_ids[restaurant], name="Purchased soup", unit_price=Decimal("6.50"), quantity=2,
        ))
        return order_id

    headers = {"Authorization": f"Bearer {create_access_token(users[0])}"}
    return client, connection, users, restaurants, headers, add_order


def test_lists_all_customers_only_in_assigned_restaurant(kitchen):
    client, connection, _, restaurants, headers, add_order = kitchen
    ids = [add_order(customer=1), add_order(customer=2)]
    add_order(restaurant=1)
    connection.execute(update(Order).where(Order.id == ids[1]).values(status="accepted"))
    response = client.get(f"/restaurants/{restaurants[0]}/orders", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert [row["id"] for row in body] == list(reversed(ids))
    assert [row["delivery_address"] for row in body] == ["Address 2", "Address 1"]
    assert body[0]["status"] == "accepted"
    for row in body:
        assert set(row) == {"id", "restaurant_id", "delivery_name", "delivery_address", "status", "total", "currency", "created_at", "items"}
        assert row["restaurant_id"] == restaurants[0]
        assert row["total"] == "13.00" and row["currency"] == "EUR"
        assert row["items"][0]["name"] == "Purchased soup"
        assert row["items"][0]["unit_price"] == "6.50"
        assert row["items"][0]["quantity"] == 2


def test_pagination_and_empty_pages(kitchen):
    client, _, _, restaurants, headers, add_order = kitchen
    url = f"/restaurants/{restaurants[0]}/orders"
    assert client.get(url, headers=headers).json() == []
    ids = [add_order() for _ in range(101)]
    for query, expected in [("", ids[::-1][:20]), ("?limit=100", ids[::-1][:100]),
                            ("?limit=20&offset=100", ids[:1]), ("?offset=10000", [])]:
        response = client.get(url + query, headers=headers)
        assert response.status_code == 200
        assert [row["id"] for row in response.json()] == expected


@pytest.mark.parametrize("problem,status", [("anonymous", 401), ("invalid", 401), ("customer", 403),
    ("admin", 403), ("removed", 403), ("other_restaurant", 403), ("missing", 404)])
def test_access_restrictions(kitchen, problem, status):
    client, connection, users, restaurants, headers, add_order = kitchen
    add_order()
    restaurant_id = restaurants[0]
    if problem == "anonymous":
        headers = {}
    elif problem == "invalid":
        headers = {"Authorization": "Bearer invalid"}
    elif problem in ("customer", "admin"):
        connection.execute(update(User).where(User.id == users[0]).values(role=problem))
    elif problem == "removed":
        connection.execute(delete(StaffAssignment).where(StaffAssignment.staff_id == users[0]))
    elif problem == "other_restaurant":
        restaurant_id = restaurants[1]
    else:
        restaurant_id = connection.scalar(select(func.max(Restaurant.id))) + 1
    response = client.get(f"/restaurants/{restaurant_id}/orders", headers=headers)
    assert response.status_code == status
    assert "Address 1" not in response.text


@pytest.mark.parametrize("query", ["limit=0", "limit=-1", "limit=101", "limit=bad", "offset=-1", "offset=10001", "offset=bad"])
def test_invalid_pagination(kitchen, query):
    client, _, _, restaurants, headers, _ = kitchen
    assert client.get(f"/restaurants/{restaurants[0]}/orders?{query}", headers=headers).status_code == 422


@pytest.mark.parametrize("restaurant_id", [0, -1, "bad", 999999999999999999])
def test_invalid_restaurant_id(kitchen, restaurant_id):
    client, _, _, _, headers, _ = kitchen
    assert client.get(f"/restaurants/{restaurant_id}/orders", headers=headers).status_code == 422
