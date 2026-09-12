from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, update

from app.auth.tokens import create_access_token
from app.models import Order, Restaurant, StaffAssignment, User

pytestmark = pytest.mark.integration
STATUSES = ["pending", "accepted", "out_for_delivery", "delivered"]


def test_admin_updates_without_assignment_but_obeys_transitions(status_order):
    client, connection, users, restaurant_id, order_id, headers = status_order
    connection.execute(update(User).where(User.id == users[0]).values(role="admin"))
    connection.execute(delete(StaffAssignment).where(StaffAssignment.staff_id == users[0]))
    url = f"/restaurants/{restaurant_id}/orders/{order_id}/status"
    assert client.patch(url, headers=headers, json={"status": "delivered"}).status_code == 409
    assert connection.scalar(select(Order.status).where(Order.id == order_id)) == "pending"
    assert client.patch(url, headers=headers, json={"status": "accepted"}).status_code == 200
    assert connection.scalar(select(Order.status).where(Order.id == order_id)) == "accepted"


@pytest.fixture
def status_order(registration, monkeypatch):
    client, connection = registration
    monkeypatch.setenv("JWT_SECRET", "order-status-test-key-with-at-least-32-characters")
    users = [connection.scalar(User.__table__.insert().values(
        email=f"{uuid4().hex}@example.com", name="Test", role=role, password_hash="unused",
    ).returning(User.id)) for role in ["staff", "customer"]]
    restaurant_id = connection.scalar(Restaurant.__table__.insert().values(name="Kitchen", address="Street").returning(Restaurant.id))
    connection.execute(StaffAssignment.__table__.insert().values(staff_id=users[0], restaurant_id=restaurant_id))
    order_id = connection.scalar(Order.__table__.insert().values(
        customer_id=users[1], restaurant_id=restaurant_id, delivery_name="Test", delivery_address="Private address",
        status="pending", total=Decimal("6.50"), currency="EUR", idempotency_key=uuid4().hex, request_fingerprint="a" * 64,
    ).returning(Order.id))
    headers = {"Authorization": f"Bearer {create_access_token(users[0])}"}
    return client, connection, users, restaurant_id, order_id, headers


@pytest.mark.parametrize("initial,target", [(a, b) for a in STATUSES for b in STATUSES])
def test_status_transition_rules(status_order, initial, target):
    client, connection, users, restaurant_id, order_id, headers = status_order
    connection.execute(update(Order).where(Order.id == order_id).values(status=initial))
    before = connection.execute(select(Order.__table__).where(Order.id == order_id)).one()._asdict()
    response = client.patch(f"/restaurants/{restaurant_id}/orders/{order_id}/status", headers=headers, json={"status": target})
    allowed = target == initial or STATUSES.index(target) == STATUSES.index(initial) + 1
    assert response.status_code == (200 if allowed else 409)
    expected = target if allowed else initial
    after = connection.execute(select(Order.__table__).where(Order.id == order_id)).one()._asdict()
    assert after == {**before, "status": expected}
    if allowed:
        assert response.json()["status"] == target
        customer_headers = {"Authorization": f"Bearer {create_access_token(users[1])}"}
        assert client.get(f"/orders/{order_id}", headers=customer_headers).json()["status"] == target


@pytest.mark.parametrize("data", [{}, {"status": "cancelled"}, {"status": None}, {"status": "accepted", "total": "1"}])
def test_invalid_status_request(status_order, data):
    client, connection, _, restaurant_id, order_id, headers = status_order
    assert client.patch(f"/restaurants/{restaurant_id}/orders/{order_id}/status", headers=headers, json=data).status_code == 422
    assert connection.scalar(select(Order.status).where(Order.id == order_id)) == "pending"


@pytest.mark.parametrize("problem,status", [("anonymous", 401), ("invalid", 401), ("customer", 403),
    ("removed", 403), ("other_restaurant", 403), ("mismatched", 404), ("missing", 404)])
def test_status_access_restrictions(status_order, problem, status):
    client, connection, users, restaurant_id, order_id, headers = status_order
    original_id = order_id
    if problem == "anonymous":
        headers = {}
    elif problem == "invalid":
        headers = {"Authorization": "Bearer invalid"}
    elif problem == "customer":
        connection.execute(update(User).where(User.id == users[0]).values(role=problem))
    elif problem == "removed":
        connection.execute(delete(StaffAssignment).where(StaffAssignment.staff_id == users[0]))
    elif problem in ("other_restaurant", "mismatched"):
        restaurant_id = connection.scalar(Restaurant.__table__.insert().values(name="Other", address="Street").returning(Restaurant.id))
        if problem == "mismatched":
            connection.execute(StaffAssignment.__table__.insert().values(staff_id=users[0], restaurant_id=restaurant_id))
    else:
        order_id = 2147483647
    response = client.patch(f"/restaurants/{restaurant_id}/orders/{order_id}/status", headers=headers, json={"status": "accepted"})
    assert response.status_code == status
    assert "Private address" not in response.text
    assert connection.scalar(select(Order.status).where(Order.id == original_id)) == "pending"


@pytest.mark.parametrize("order_id", [0, -1, "bad", 99999999999999999])
def test_invalid_order_id(status_order, order_id):
    client, _, _, restaurant_id, _, headers = status_order
    assert client.patch(f"/restaurants/{restaurant_id}/orders/{order_id}/status", headers=headers,
                        json={"status": "accepted"}).status_code == 422
