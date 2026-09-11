from typing import Annotated

from pydantic import BaseModel, Field, SecretStr, StringConstraints

from app.auth.schemas import EmailRequest


class StaffCreate(EmailRequest):
    password: SecretStr = Field(min_length=8, max_length=128)
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ]


class AssignmentResponse(BaseModel):
    staff_id: int
    restaurant_id: int
