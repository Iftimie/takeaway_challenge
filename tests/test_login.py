from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from sqlalchemy import delete, update

from app.auth.service import password_hasher
from app.auth.tokens import create_access_token
from app.models import User

pytestmark = pytest.mark.integration
TEST_KEY = "test-only-jwt-key-not-for-production-123456789-abcdefghijklmnopqrstuvwxyz"
PASSWORD = "a long test passphrase"


@pytest.fixture(autouse=True)
def jwt_settings(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_KEY)
    monkeypatch.setenv("ACCESS_TOKEN_MINUTES", "30")


def add_user(connection, role="customer"):
    email = f"Login.{uuid4().hex}+tag@example.com"
    user_id = connection.scalar(User.__table__.insert().values(
        email=email, name="Test Login", role=role,
        password_hash=password_hasher.hash(PASSWORD),
    ).returning(User.id))
    return user_id, email


@pytest.mark.parametrize("role", ["customer", "staff", "admin"])
def test_login_and_me_for_every_role(registration, role):
    client, connection = registration
    user_id, email = add_user(connection, role)
    response = client.post("/auth/login", json={
        "email": f"  {email.upper()}  ", "password": PASSWORD,
    })
    assert response.status_code == 200
    assert set(response.json()) == {"access_token", "token_type"}
    assert response.json()["token_type"] == "bearer"
    token = response.json()["access_token"]
    claims = jwt.decode(token, TEST_KEY, algorithms=["HS256"])
    assert set(claims) == {"sub", "iat", "exp"}
    assert claims["sub"] == str(user_id)
    assert claims["exp"] - claims["iat"] == 1800
    profile = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json() == {
        "id": user_id, "email": email, "name": "Test Login",
        "role": role, "default_address": None,
    }


def test_wrong_password_and_unknown_email_have_same_response(registration):
    client, connection = registration
    _, email = add_user(connection)
    wrong = client.post("/auth/login", json={"email": email, "password": "wrong"})
    unknown = client.post("/auth/login", json={
        "email": f"missing-{uuid4().hex}@example.com", "password": PASSWORD,
    })
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Invalid email or password"}
    assert wrong.headers["www-authenticate"] == unknown.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("authorization", [None, "Basic abc", "Bearer", "Bearer not-a-jwt"])
def test_me_rejects_missing_or_malformed_credentials(registration, authorization):
    client, _ = registration
    headers = {} if authorization is None else {"Authorization": authorization}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("problem", [
    "expired", "signature", "algorithm", "missing_exp", "missing_sub", "missing_iat",
    "bad_sub", "oversized_sub", "null_exp", "future_iat",
])
def test_me_rejects_invalid_tokens(registration, problem):
    client, connection = registration
    user_id, _ = add_user(connection)
    now = datetime.now(timezone.utc)
    claims = {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=30)}
    if problem == "expired":
        claims["iat"] = now - timedelta(hours=1)
        claims["exp"] = now - timedelta(seconds=1)
    elif problem.startswith("missing_"):
        del claims[problem.removeprefix("missing_")]
    elif problem == "bad_sub":
        claims["sub"] = "not-an-id"
    elif problem == "oversized_sub":
        claims["sub"] = "99999999999999999999999999"
    elif problem == "null_exp":
        claims["exp"] = None
    elif problem == "future_iat":
        claims["iat"] = now + timedelta(minutes=5)
    token = jwt.encode(
        claims, "different-key-not-used-by-server-123456789" if problem == "signature" else TEST_KEY,
        algorithm="HS384" if problem == "algorithm" else "HS256",
    )
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired access token"}


def test_me_uses_current_user_and_rejects_deleted_user(registration):
    client, connection = registration
    user_id, _ = add_user(connection)
    headers = {"Authorization": f"Bearer {create_access_token(user_id)}"}
    connection.execute(update(User).where(User.id == user_id).values(name="Updated Name"))
    assert client.get("/users/me", headers=headers).json()["name"] == "Updated Name"
    connection.execute(delete(User).where(User.id == user_id))
    assert client.get("/users/me", headers=headers).status_code == 401


@pytest.mark.parametrize("data", [
    {}, {"email": "bad", "password": PASSWORD},
    {"email": "a@example.com", "password": "x" * 129},
    {"email": "a@example.com", "password": PASSWORD, "role": "admin"},
])
def test_invalid_login_payload(registration, data):
    client, _ = registration
    response = client.post("/auth/login", json=data)
    assert response.status_code == 422
    assert PASSWORD not in response.text
    assert all(set(item) == {"loc", "msg", "type"} for item in response.json()["detail"])
