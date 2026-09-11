from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models import MenuItem, Order, OrderItem, Restaurant, User

pytestmark = pytest.mark.integration


@pytest.fixture
def order_data(registration):
    _, connection = registration
    customer_id = connection.scalar(User.__table__.insert().values(
        email=f"{uuid4().hex}@example.com", name="Customer", role="customer",
        password_hash="unused").returning(User.id))
    restaurant_id = connection.scalar(Restaurant.__table__.insert().values(
        name="Kitchen", address="Street").returning(Restaurant.id))
    menu_id = connection.scalar(MenuItem.__table__.insert().values(
        restaurant_id=restaurant_id, name="Soup", price=Decimal("6.50"), available=True,
    ).returning(MenuItem.id))
    data = dict(customer_id=customer_id, restaurant_id=restaurant_id,
                delivery_name="Customer", delivery_address="12 Street", status="pending",
                total=Decimal("13.00"), currency="EUR", idempotency_key=uuid4().hex,
                request_fingerprint="a" * 64)
    return connection, menu_id, data


def add_order(connection, data):
    return connection.scalar(Order.__table__.insert().values(**data).returning(Order.id))


def item_data(order_id, menu_id):
    return dict(order_id=order_id, menu_item_id=menu_id, name="Soup", unit_price=Decimal("6.50"), quantity=2)


def test_snapshots_survive_menu_and_customer_changes(order_data):
    connection, menu_id, data = order_data
    order_id = add_order(connection, data)
    connection.execute(OrderItem.__table__.insert().values(**item_data(order_id, menu_id)))
    connection.execute(update(MenuItem).where(MenuItem.id == menu_id).values(name="New soup", price=Decimal("9.00")))
    connection.execute(update(User).where(User.id == data["customer_id"]).values(name="New name", default_address="Other street"))
    order = connection.execute(select(Order.__table__).where(Order.id == order_id)).one()
    item = connection.execute(select(OrderItem.__table__).where(OrderItem.order_id == order_id)).one()
    assert (order.delivery_name, order.delivery_address, order.total, order.currency) == ("Customer", "12 Street", Decimal("13.00"), "EUR")
    assert order.created_at.tzinfo is not None
    assert order.request_fingerprint == data["request_fingerprint"]
    assert (item.name, item.unit_price, item.quantity) == ("Soup", Decimal("6.50"), 2)


def test_idempotency_key_is_unique_per_customer(order_data):
    connection, _, data = order_data
    add_order(connection, data)
    with pytest.raises(IntegrityError), connection.begin_nested():
        add_order(connection, data)
    other_customer = connection.scalar(User.__table__.insert().values(
        email=f"{uuid4().hex}@example.com", name="Other", role="customer", password_hash="unused",
    ).returning(User.id))
    assert add_order(connection, {**data, "customer_id": other_customer})
    assert add_order(connection, {**data, "idempotency_key": "another-key"})


@pytest.mark.parametrize("status", ["pending", "accepted", "out_for_delivery", "delivered"])
def test_allowed_statuses(order_data, status):
    connection, _, data = order_data
    assert add_order(connection, {**data, "status": status})


@pytest.mark.parametrize("field,value", [
    ("status", "cancelled"), ("total", Decimal("0")), ("total", Decimal("-1")),
    ("total", Decimal("NaN")), ("currency", "USD"), ("delivery_name", " "),
    ("delivery_address", " "), ("idempotency_key", " "), ("request_fingerprint", "bad"),
    ("customer_id", -1), ("restaurant_id", -1),
])
def test_order_constraints(order_data, field, value):
    connection, _, data = order_data
    with pytest.raises(IntegrityError), connection.begin_nested():
        add_order(connection, {**data, field: value})


@pytest.mark.parametrize("field", ["customer_id", "restaurant_id", "delivery_name", "delivery_address", "status", "total", "currency", "idempotency_key", "request_fingerprint"])
def test_order_required_fields(order_data, field):
    connection, _, data = order_data
    with pytest.raises(IntegrityError), connection.begin_nested():
        add_order(connection, {**data, field: None})


@pytest.mark.parametrize("field,value", [
    ("quantity", 0), ("quantity", -1), ("unit_price", Decimal("0")),
    ("unit_price", Decimal("-1")), ("unit_price", Decimal("NaN")),
    ("name", " "), ("order_id", -1), ("menu_item_id", -1),
    ("quantity", None), ("unit_price", None), ("name", None),
])
def test_item_constraints(order_data, field, value):
    connection, menu_id, data = order_data
    order_id = add_order(connection, data)
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(OrderItem.__table__.insert().values(**{**item_data(order_id, menu_id), field: value}))


def test_one_line_per_menu_item(order_data):
    connection, menu_id, data = order_data
    order_id = add_order(connection, data)
    values = item_data(order_id, menu_id)
    connection.execute(OrderItem.__table__.insert().values(**values))
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(OrderItem.__table__.insert().values(**values))
