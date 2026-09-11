from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.auth.service import password_hasher
from app.auth.tokens import create_access_token
from app.models import Restaurant, StaffAssignment, User

pytestmark = pytest.mark.integration
PASSWORD = "staff initial password"


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-only-staff-key-with-at-least-32-characters")


def add_user(connection, role="staff"):
    return connection.scalar(User.__table__.insert().values(
        email=f"{uuid4().hex}@example.com", name="Test User",
        role=role, password_hash="unchanged-hash",
    ).returning(User.id))


def headers(connection, role="admin"):
    return {"Authorization": f"Bearer {create_access_token(add_user(connection, role))}"}


def add_restaurant(connection):
    return connection.scalar(Restaurant.__table__.insert().values(
        name="Kitchen", address="Street",
    ).returning(Restaurant.id))


def payload():
    return {"email": f"{uuid4().hex}@example.com", "name": "Staff", "password": PASSWORD}


def test_create_staff_and_login(registration):
    client, connection = registration
    data = payload()
    data["email"] = "  " + data["email"].upper() + "  "
    data["name"] = " Staff "
    response = client.post("/staff", headers=headers(connection), json=data)
    assert response.status_code == 201
    body = response.json()
    assert body == {"id": body["id"], "email": data["email"].strip().lower(),
                    "name": "Staff", "role": "staff", "default_address": None}
    stored = connection.scalar(select(User.password_hash).where(User.id == body["id"]))
    assert stored != PASSWORD
    assert password_hasher.verify(PASSWORD, stored)
    login = client.post("/auth/login", json={"email": body["email"], "password": PASSWORD})
    assert login.status_code == 200
    me = client.get("/users/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.json() == body


@pytest.mark.parametrize("role", ["customer", "staff", "admin"])
def test_duplicate_email_preserves_existing_account(registration, role):
    client, connection = registration
    user_id = add_user(connection, role)
    before = connection.execute(select(User.__table__).where(User.id == user_id)).one()
    data = payload()
    data["email"] = before.email.upper()
    response = client.post("/staff", headers=headers(connection), json=data)
    assert response.status_code == 409
    assert connection.execute(select(User.__table__).where(User.id == user_id)).one() == before


@pytest.mark.parametrize("field,value", [
    ("email", "bad"), ("name", " "), ("password", "tiny"),
    ("password", "x" * 129), ("name", "x" * 201), ("role", "admin"),
    ("default_address", "Street"),
])
def test_invalid_staff_input_creates_no_user(registration, field, value):
    client, connection = registration
    auth = headers(connection)
    before = connection.scalar(select(func.count()).select_from(User))
    data = payload()
    data[field] = value
    response = client.post("/staff", headers=auth, json=data)
    assert response.status_code == 422
    assert data["password"] not in response.text
    assert connection.scalar(select(func.count()).select_from(User)) == before


@pytest.mark.parametrize("role,status", [(None, 401), ("customer", 403), ("staff", 403)])
@pytest.mark.parametrize("operation", ["create", "assign"])
def test_admin_required(registration, role, status, operation):
    client, connection = registration
    staff_id = add_user(connection)
    restaurant_id = add_restaurant(connection)
    auth = headers(connection, role) if role else {}
    before = connection.scalar(select(func.count()).select_from(User))
    assignments = connection.scalar(select(func.count()).select_from(StaffAssignment))
    if operation == "create":
        response = client.post("/staff", headers=auth, json=payload())
    else:
        response = client.post(f"/staff/{staff_id}/restaurants/{restaurant_id}", headers=auth)
    assert response.status_code == status
    assert connection.scalar(select(func.count()).select_from(User)) == before
    assert connection.scalar(select(func.count()).select_from(StaffAssignment)) == assignments


def test_assignments_and_duplicate(registration):
    client, connection = registration
    auth = headers(connection)
    staff_a, staff_b = add_user(connection), add_user(connection)
    restaurant_a, restaurant_b = add_restaurant(connection), add_restaurant(connection)
    for staff_id, restaurant_id in [(staff_a, restaurant_a), (staff_a, restaurant_b), (staff_b, restaurant_a)]:
        response = client.post(f"/staff/{staff_id}/restaurants/{restaurant_id}", headers=auth)
        assert response.status_code == 201
        assert response.json() == {"staff_id": staff_id, "restaurant_id": restaurant_id}
    duplicate = client.post(f"/staff/{staff_a}/restaurants/{restaurant_a}", headers=auth)
    assert duplicate.status_code == 409
    assert duplicate.json() == {"detail": "Staff already assigned to restaurant"}
    assert connection.scalar(select(func.count()).select_from(StaffAssignment).where(
        StaffAssignment.staff_id.in_([staff_a, staff_b]))) == 3


@pytest.mark.parametrize("problem,status", [("staff", 404), ("restaurant", 404), ("customer", 409), ("admin", 409)])
def test_invalid_assignment_creates_no_row(registration, problem, status):
    client, connection = registration
    auth = headers(connection)
    staff_id = add_user(connection, problem if problem in ("customer", "admin") else "staff")
    restaurant_id = add_restaurant(connection)
    if problem == "staff":
        staff_id = connection.scalar(select(func.max(User.id))) + 1
    if problem == "restaurant":
        restaurant_id = connection.scalar(select(func.max(Restaurant.id))) + 1
    before = connection.scalar(select(func.count()).select_from(StaffAssignment))
    response = client.post(f"/staff/{staff_id}/restaurants/{restaurant_id}", headers=auth)
    assert response.status_code == status
    assert connection.scalar(select(func.count()).select_from(StaffAssignment)) == before


@pytest.mark.parametrize("staff_id,restaurant_id", [(0, 1), (1, -1), ("bad", 1), (1, 999999999999999999)])
def test_invalid_assignment_ids(registration, staff_id, restaurant_id):
    client, connection = registration
    assert client.post(f"/staff/{staff_id}/restaurants/{restaurant_id}", headers=headers(connection)).status_code == 422


@pytest.mark.parametrize("problem", ["duplicate", "missing_staff", "missing_restaurant"])
def test_assignment_database_constraints(registration, problem):
    _, connection = registration
    staff_id, restaurant_id = add_user(connection), add_restaurant(connection)
    connection.execute(StaffAssignment.__table__.insert().values(staff_id=staff_id, restaurant_id=restaurant_id))
    if problem == "missing_staff":
        staff_id = connection.scalar(select(func.max(User.id))) + 1
    if problem == "missing_restaurant":
        restaurant_id = connection.scalar(select(func.max(Restaurant.id))) + 1
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(StaffAssignment.__table__.insert().values(staff_id=staff_id, restaurant_id=restaurant_id))
