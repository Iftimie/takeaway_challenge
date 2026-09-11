from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import MenuItem, Restaurant

pytestmark = pytest.mark.integration


def add_restaurant(connection):
    return connection.scalar(Restaurant.__table__.insert().values(
        name="Kitchen", address="Street",
    ).returning(Restaurant.id))


def add_items(connection, restaurant_id, count):
    return [connection.scalar(MenuItem.__table__.insert().values(
        restaurant_id=restaurant_id, name=f"Item {number}",
        price=Decimal("12.50"), available=number % 2 == 0,
    ).returning(MenuItem.id)) for number in range(count)]


def test_public_menu_returns_only_restaurant_items(registration):
    client, connection = registration
    restaurant_id, other_id = add_restaurant(connection), add_restaurant(connection)
    add_items(connection, other_id, 1)
    ids = add_items(connection, restaurant_id, 2)
    response = client.get(f"/restaurants/{restaurant_id}/menu-items")
    assert response.status_code == 200
    assert response.json() == [
        {"id": item_id, "restaurant_id": restaurant_id, "name": f"Item {number}",
         "price": "12.50", "currency": "EUR", "available": number == 0}
        for number, item_id in enumerate(ids)
    ]


def test_default_page_and_offset(registration):
    client, connection = registration
    restaurant_id = add_restaurant(connection)
    ids = add_items(connection, restaurant_id, 23)
    url = f"/restaurants/{restaurant_id}/menu-items"
    first = client.get(url)
    second = client.get(url, params={"limit": 20, "offset": 20})
    assert first.status_code == second.status_code == 200
    assert [item["id"] for item in first.json()] == ids[:20]
    assert [item["id"] for item in second.json()] == ids[20:]


def test_maximum_page_size(registration):
    client, connection = registration
    restaurant_id = add_restaurant(connection)
    ids = add_items(connection, restaurant_id, 101)
    response = client.get(f"/restaurants/{restaurant_id}/menu-items", params={"limit": 100})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ids[:100]


@pytest.mark.parametrize("count,offset", [(0, 0), (2, 2), (2, 10000)])
def test_empty_page(registration, count, offset):
    client, connection = registration
    restaurant_id = add_restaurant(connection)
    add_items(connection, restaurant_id, count)
    response = client.get(f"/restaurants/{restaurant_id}/menu-items", params={"offset": offset})
    assert response.status_code == 200
    assert response.json() == []


def test_missing_restaurant(registration):
    client, connection = registration
    missing_id = (connection.scalar(select(func.max(Restaurant.id))) or 0) + 1
    response = client.get(f"/restaurants/{missing_id}/menu-items")
    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant not found"}


@pytest.mark.parametrize("params", [
    {"limit": 0}, {"limit": -1}, {"limit": 101}, {"limit": "bad"},
    {"offset": -1}, {"offset": 10001}, {"offset": "bad"},
])
def test_invalid_pagination(registration, params):
    client, connection = registration
    restaurant_id = add_restaurant(connection)
    assert client.get(f"/restaurants/{restaurant_id}/menu-items", params=params).status_code == 422


@pytest.mark.parametrize("restaurant_id", [0, -1, "bad", 99999999999999999999])
def test_invalid_restaurant_id(registration, restaurant_id):
    client, _ = registration
    assert client.get(f"/restaurants/{restaurant_id}/menu-items").status_code == 422
