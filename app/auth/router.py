from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.schemas import RegisterRequest, UserResponse
from app.auth.service import EmailAlreadyRegistered, register_customer
from app.db import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest, session: Annotated[Session, Depends(get_session)]
) -> UserResponse:
    try:
        return register_customer(session, data)
    except EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from None
