from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.models import User

from app.payload_logging import PayloadLoggingRoute

router = APIRouter(prefix="/users", tags=["users"], route_class=PayloadLoggingRoute)


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
