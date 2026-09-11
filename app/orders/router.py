from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_session
from app.models import User
from app.orders.schemas import OrderCreate, OrderResponse
from app.orders.service import OrderProblem, create_order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201,
             responses={200: {"model": OrderResponse, "description": "Existing order returned for a retry"}})
def place_order(
    data: OrderCreate,
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    idempotency_key: Annotated[str, Header(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")],
) -> OrderResponse:
    try:
        result, created = create_order(session, user.id, idempotency_key, data)
    except OrderProblem as error:
        raise HTTPException(error.status_code, error.detail) from None
    response.status_code = 201 if created else 200
    return result
