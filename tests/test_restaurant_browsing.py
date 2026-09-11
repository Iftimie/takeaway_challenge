import pytest
from sqlalchemy import func, select

from app.models import Restaurant

pytestmark = pytest.mark.integration


def add_restaurants(connection, count):
    return [connection.scalar(Restaurant.__table__.insert().values(
        name=f"Kitchen {number}", address=f"Street {number}",
    ).returning(Restaurant.id)) for number in range(count)]


def test_public_list_has_default_limit_and_id_order(registration):
    client, connection = registration
    existing_ids = list(connection.scalars(select(Restaurant.id).order_by(Restaurant.id)))
    new_ids = add_restaurants(connection, 25)
    response = client.get("/restaurants")
    assert response.status_code == 200
    assert len(response.json()) == 20
    assert [item["id"] for item in response.json()] == sorted(existing_ids + new_ids)[:20]
    assert all(set(item) == {"id", "name", "address"} for item in response.json())


def test_offset_pages_do_not_overlap(registration):
    client, connection = registration
    offset = connection.scalar(select(func.count()).select_from(Restaurant))
    ids = add_restaurants(connection, 3)
    first = client.get("/restaurants", params={"limit": 2, "offset": offset})
    second = client.get("/restaurants", params={"limit": 2, "offset": offset + 2})
    assert first.status_code == second.status_code == 200
    assert [item["id"] for item in first.json()] == ids[:2]
    assert [item["id"] for item in second.json()] == ids[2:]


def test_empty_page_returns_empty_list(registration):
    client, connection = registration
    offset = connection.scalar(select(func.count()).select_from(Restaurant))
    response = client.get("/restaurants", params={"offset": offset})
    assert response.status_code == 200
    assert response.json() == []


def test_maximum_page_size_is_accepted(registration):
    client, connection = registration
    offset = connection.scalar(select(func.count()).select_from(Restaurant))
    ids = add_restaurants(connection, 101)
    response = client.get("/restaurants", params={"limit": 100, "offset": offset})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ids[:100]


@pytest.mark.parametrize("params", [
    {"limit": 0}, {"limit": -1}, {"limit": 101}, {"limit": "bad"},
    {"offset": -1}, {"offset": 10001}, {"offset": "bad"},
])
def test_invalid_pagination_is_rejected(registration, params):
    client, _ = registration
    assert client.get("/restaurants", params=params).status_code == 422


def test_public_restaurant_detail(registration):
    client, connection = registration
    restaurant_id = add_restaurants(connection, 1)[0]
    response = client.get(f"/restaurants/{restaurant_id}")
    assert response.status_code == 200
    assert response.json() == {"id": restaurant_id, "name": "Kitchen 0", "address": "Street 0"}


def test_missing_restaurant_returns_404(registration):
    client, connection = registration
    missing_id = (connection.scalar(select(func.max(Restaurant.id))) or 0) + 1
    response = client.get(f"/restaurants/{missing_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant not found"}


@pytest.mark.parametrize("restaurant_id", ["0", "-1", "bad", "99999999999999999999"])
def test_invalid_restaurant_id_returns_422(registration, restaurant_id):
    client, _ = registration
    assert client.get(f"/restaurants/{restaurant_id}").status_code == 422
