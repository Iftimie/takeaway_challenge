from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StringConstraints


class MenuItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ]
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2, allow_inf_nan=False)
    available: StrictBool = True


class MenuItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    price: Decimal
    available: bool
    currency: Literal["EUR"] = "EUR"
