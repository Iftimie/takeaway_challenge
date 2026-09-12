from typing import Annotated

from fastapi import Depends, HTTPException, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.auth.tokens import decode_user_id
from app.db import get_session
from app.models import Restaurant, StaffAssignment, User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        user_id = decode_user_id(credentials.credentials)
    except InvalidTokenError:
        raise unauthorized from None
    user = session.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_assigned_staff(
    restaurant_id: Annotated[int, Path(ge=1, le=2147483647)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    if user.role not in {"staff", "admin"}:
        raise HTTPException(403, "Assigned staff or admin access required")

    if session.get(Restaurant, restaurant_id) is None:
        raise HTTPException(404, "Restaurant not found")

    if user.role == "admin":
        return

    if session.get(StaffAssignment, (user.id, restaurant_id)) is None:
        raise HTTPException(403, "Assigned staff access required")
