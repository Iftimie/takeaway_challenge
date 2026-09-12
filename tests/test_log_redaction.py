import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.log_redaction import to_log_dict
from app.orders.schemas import OrderCreate, OrderResponse
from app.staff.schemas import StaffCreate


@pytest.mark.parametrize("schema", [RegisterRequest, StaffCreate])
def test_account_requests_redact_inherited_and_own_fields(schema):
    model = schema(email="private@example.com", password="private password", name="Private Name")
    logged = to_log_dict(model)
    assert logged["email"] == "private@example.com"
    assert logged["password"] == logged["name"] == "[REDACTED]"
    assert "private password" not in json.dumps(logged)


def test_login_and_token_redaction_preserve_normal_serialization():
    login = LoginRequest(email="private@example.com", password="private password")
    token = TokenResponse(access_token="private-token")
    assert to_log_dict(login) == {"email": "private@example.com", "password": "[REDACTED]"}
    assert to_log_dict(token) == {"access_token": "[REDACTED]", "token_type": "bearer"}
    assert login.password.get_secret_value() == "private password"
    assert token.model_dump(mode="json")["access_token"] == "private-token"


def test_user_response_redaction():
    user = UserResponse(id=1, email="private@example.com", name="Private Name", role="customer", default_address="Private Street")
    assert to_log_dict(user) == {"id": 1, "email": "private@example.com", "name": "[REDACTED]", "role": "customer", "default_address": "[REDACTED]"}
    assert user.model_dump()["default_address"] == "Private Street"


def test_order_request_preserves_safe_nested_values():
    order = OrderCreate(restaurant_id=12, delivery_name="Private Name", delivery_address="Private Street",
                        items=[{"menu_item_id": 42, "quantity": 2}])
    before = order.model_dump()
    logged = to_log_dict(order)
    assert logged == {"restaurant_id": 12, "delivery_name": "[REDACTED]", "delivery_address": "[REDACTED]",
                      "items": [{"menu_item_id": 42, "quantity": 2}]}
    logged["items"][0]["quantity"] = 99
    assert order.model_dump() == before


def test_response_list_redacts_nested_models_and_encodes_decimals():
    class Page(BaseModel):
        orders: list[OrderResponse]

    order = OrderResponse(id=1, restaurant_id=12, delivery_name="Private Name", delivery_address="Private Street",
        status="pending", total=Decimal("13.00"), currency="EUR", created_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
        items=[{"menu_item_id": 42, "name": "Soup", "unit_price": Decimal("6.50"), "quantity": 2}])
    page = Page(orders=[order])
    before = page.model_dump_json()
    logged = to_log_dict(page)
    assert "Private" not in json.dumps(logged)
    result = logged["orders"][0]
    assert result["delivery_name"] == result["delivery_address"] == "[REDACTED]"
    assert result["total"] == "13.00"
    assert result["created_at"] == "2026-09-12T00:00:00+00:00"
    assert result["items"] == [{"menu_item_id": 42, "name": "Soup", "unit_price": "6.50", "quantity": 2}]
    assert page.model_dump_json() == before


def test_whole_field_redaction_and_secret_type_fallback():
    class Example(BaseModel):
        credentials: list[str] = Field(json_schema_extra={"sensitive": True})
        secret: SecretStr
        missing: str | None = Field(default=None, json_schema_extra={"sensitive": True})

    assert to_log_dict(Example(credentials=["private"], secret="private")) == {
        "credentials": "[REDACTED]", "secret": "[REDACTED]", "missing": "[REDACTED]"}


def test_extra_fields_and_untyped_dict_are_not_serialized():
    class Example(BaseModel):
        model_config = ConfigDict(extra="allow")
        count: int
        unstructured: dict

    model = Example(count=2, unstructured={"password": "private"}, secret_extra="private")
    assert to_log_dict(model) == {"count": 2, "unstructured": "[OMITTED]"}


def test_raw_dictionary_rejected():
    with pytest.raises(TypeError, match="Pydantic model"):
        to_log_dict({"password": "private"})
