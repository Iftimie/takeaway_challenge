import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.orders.schemas import OrderCreate, OrderResponse
from app.payload_logging import PayloadLoggingRoute, payload_for_log
from app.request_logging import RequestLoggingMiddleware, logger


@pytest.fixture
def payload_app(caplog):
    app = FastAPI()
    app.router.route_class = PayloadLoggingRoute
    app.add_middleware(RequestLoggingMiddleware)
    logger.addHandler(caplog.handler)
    try:
        yield app, caplog
    finally:
        logger.removeHandler(caplog.handler)


def last_record(caplog):
    return json.loads([record for record in caplog.records if record.name == logger.name][-1].message)


def test_registration_request_and_response_use_schema_policy(payload_app):
    app, logs = payload_app

    @app.post("/register", response_model=UserResponse, status_code=201)
    def register(data: RegisterRequest):
        return UserResponse(id=1, email=str(data.email), name=data.name, role="customer", default_address=data.default_address)

    with TestClient(app) as client:
        response = client.post("/register", json={"email": "visible@example.com", "password": "private-password",
            "name": "Private Name", "default_address": "Private Street"})
    entry = last_record(logs)
    assert response.status_code == 201 and response.json()["name"] == "Private Name"
    assert entry["request_body"] == {"email": "visible@example.com", "password": "[REDACTED]",
                                     "name": "[REDACTED]", "default_address": "[REDACTED]"}
    assert entry["response_body"]["email"] == "visible@example.com"
    assert entry["response_body"]["name"] == entry["response_body"]["default_address"] == "[REDACTED]"
    for value in ["private-password", "Private Name", "Private Street"]:
        assert value not in json.dumps(entry)


@pytest.mark.parametrize("fail", [False, True])
def test_login_redacts_password_and_token_or_error_details(payload_app, fail):
    app, logs = payload_app

    @app.post("/login", response_model=TokenResponse)
    def login(data: LoginRequest):
        if fail:
            raise HTTPException(401, "private-error")
        return TokenResponse(access_token="private-token")

    with TestClient(app) as client:
        response = client.post("/login", json={"email": "visible@example.com", "password": "private-password"})
    entry = last_record(logs)
    assert response.status_code == (401 if fail else 200)
    assert entry["request_body"] == {"email": "visible@example.com", "password": "[REDACTED]"}
    assert entry["response_body"] == ({"omitted": "error_response"} if fail else
                                      {"access_token": "[REDACTED]", "token_type": "bearer"})
    assert all(value not in json.dumps(entry) for value in ["private-password", "private-token", "private-error"])
    if not fail:
        assert response.json()["access_token"] == "private-token"


def test_order_and_list_responses_preserve_safe_item_context(payload_app):
    app, logs = payload_app
    order = OrderResponse(id=1, restaurant_id=2, delivery_name="Private Name", delivery_address="Private Street",
        status="pending", total=Decimal("5.00"), currency="EUR", created_at=datetime.now(timezone.utc),
        items=[{"menu_item_id": 3, "name": "Soup", "unit_price": "2.50", "quantity": 2}])

    @app.post("/orders", response_model=OrderResponse)
    def create(data: OrderCreate):
        return order

    @app.get("/orders", response_model=list[OrderResponse])
    def orders():
        return [order]

    with TestClient(app) as client:
        client.post("/orders", json={"restaurant_id": 2, "delivery_name": "Private Name", "delivery_address": "Private Street",
                                     "items": [{"menu_item_id": 3, "quantity": 2}]})
        entry = last_record(logs)
        assert entry["request_body"]["items"] == [{"menu_item_id": 3, "quantity": 2}]
        assert entry["request_body"]["delivery_name"] == "[REDACTED]"
        assert entry["response_body"]["total"] == "5.00"
        response = client.get("/orders")
    entry = last_record(logs)
    assert entry["response_body"][0]["delivery_address"] == "[REDACTED]"
    assert entry["response_body"][0]["items"][0]["name"] == "Soup"
    assert response.json()[0]["delivery_address"] == "Private Street"


@pytest.mark.parametrize("raw", ['{"email":', '{"email":"invalid-private-email","password":"x"}',
                                 '{"email":"visible@example.com","password":"valid-password","private-extra-key":"private-value"}'])
def test_invalid_input_logs_only_safe_validation_context(payload_app, raw):
    app, logs = payload_app

    @app.post("/login", response_model=TokenResponse)
    def login(data: LoginRequest):
        return TokenResponse(access_token="secret")

    with TestClient(app) as client:
        assert client.post("/login", content=raw, headers={"Content-Type": "application/json"}).status_code == 422
    entry = last_record(logs)
    assert entry["request_body"] == {"omitted": "validation_failed"}
    assert entry["validation_errors"]
    assert all(set(error) == {"loc", "type"} for error in entry["validation_errors"])
    assert all(value not in json.dumps(entry) for value in ["invalid-private-email", "valid-password", "private-extra-key", "private-value"])


def test_payload_size_limit_keeps_actual_response(payload_app):
    app, logs = payload_app

    class Content(BaseModel):
        text: str

    @app.post("/echo", response_model=Content)
    def echo(data: Content):
        return data

    with TestClient(app) as client:
        response = client.post("/echo", json={"text": "é" * 3000})
    assert response.json() == {"text": "é" * 3000}
    entry = last_record(logs)
    assert entry["request_body"] == entry["response_body"] == {"omitted": "size_limit"}


def test_size_limit_applies_after_redaction():
    class Content(BaseModel):
        secret: str = Field(json_schema_extra={"sensitive": True})
    assert payload_for_log(json.dumps({"secret": "x" * 5000}).encode(), Content) == {"secret": "[REDACTED]"}
    assert payload_for_log(json.dumps({"secret": "x" * 70000}).encode(), Content) == {"omitted": "size_limit"}


def test_untyped_payloads_are_omitted(payload_app):
    app, logs = payload_app

    @app.post("/untyped")
    def untyped(data: dict):
        return data

    with TestClient(app) as client:
        assert client.post("/untyped", json={"secret": "private-value"}).json() == {"secret": "private-value"}
    entry = last_record(logs)
    assert entry["request_body"] == entry["response_body"] == {"omitted": "no_schema"}


def test_unexpected_exception_never_logs_raw_body_or_message(payload_app):
    app, logs = payload_app

    @app.post("/fail", response_model=TokenResponse)
    def fail(data: LoginRequest):
        raise RuntimeError("private-exception")

    with TestClient(app) as client:
        response = client.post("/fail", json={"email": "visible@example.com", "password": "private-password"})
    entry = last_record(logs)
    assert response.status_code == 500
    assert entry["error_type"] == "RuntimeError"
    assert all(value not in json.dumps(entry) for value in ["private-exception", "private-password"])


def test_response_that_does_not_match_schema_is_omitted():
    assert payload_for_log(b'{"unexpected":"private-value"}', TokenResponse) == {"omitted": "invalid_payload"}
