from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.schemas import RegisterRequest, UserResponse
from app.models import User

password_hasher = PasswordHash.recommended()


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
