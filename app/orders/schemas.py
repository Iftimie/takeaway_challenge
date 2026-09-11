from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

PositiveId = Annotated[int, Field(strict=True, ge=1, le=2147483647)]


class OrderLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    menu_item_id: PositiveId
    quantity: int = Field(strict=True, ge=1, le=100)


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    restaurant_id: PositiveId
    delivery_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    delivery_address: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    items: list[OrderLineCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def distinct_items(self) -> Self:
        ids = [item.menu_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Each menu item must appear once; use quantity for multiple units")
        return self


class OrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    menu_item_id: int
    name: str
    unit_price: Decimal
    quantity: int


class OrderResponse(BaseModel):
    id: int
    restaurant_id: int
    delivery_name: str
    delivery_address: str
    status: str
    total: Decimal
    currency: str
    created_at: datetime
    items: list[OrderLineResponse]


class OrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    status: str
    total: Decimal
    currency: str
    created_at: datetime
