from secrets import token_urlsafe

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, RegisterRequest, UserResponse
from app.models import User

password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash(token_urlsafe(32))


def authenticate_user(session: Session, data: LoginRequest) -> User | None:
    user = session.scalar(select(User).where(func.lower(User.email) == str(data.email)))
    # Verify a hash even for unknown emails, avoiding a cheap early exit.
    stored_hash = user.password_hash if user is not None else dummy_hash
    try:
        valid = password_hasher.verify(data.password.get_secret_value(), stored_hash)
    except UnknownHashError:
        valid = False
    return user if valid else None


class EmailAlreadyRegistered(Exception):
    pass


def register_customer(session: Session, data: RegisterRequest) -> UserResponse:
    user = User(
        email=str(data.email),
        password_hash=password_hasher.hash(data.password.get_secret_value()),
        name=data.name,
        default_address=data.default_address,
        role="customer",
    )
    session.add(user)
    try:
        session.flush()
        response = UserResponse.model_validate(user)
        session.commit()
    except IntegrityError as error:
        session.rollback()
        diagnostic = getattr(error.orig, "diag", None)
        if getattr(diagnostic, "constraint_name", None) == "uq_users_email":
            raise EmailAlreadyRegistered from error
        raise
    return response
