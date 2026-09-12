from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
    field_validator,
)


class EmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=320, json_schema_extra={})

    @field_validator("email", mode="before")
    @classmethod
    def trim_email(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()


class RegisterRequest(EmailRequest):
    password: SecretStr = Field(min_length=8, max_length=128, json_schema_extra={"sensitive": True})
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ] = Field(json_schema_extra={"sensitive": True})
    default_address: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ] | None = Field(default=None, json_schema_extra={"sensitive": True})


class LoginRequest(EmailRequest):
    password: SecretStr = Field(min_length=1, max_length=128, json_schema_extra={"sensitive": True})


class TokenResponse(BaseModel):
    access_token: str = Field(json_schema_extra={"sensitive": True})
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str = Field(json_schema_extra={})
    name: str = Field(json_schema_extra={"sensitive": True})
    role: str
    default_address: str | None = Field(json_schema_extra={"sensitive": True})
