from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_session
from app.models import Order, User
from app.orders.schemas import OrderCreate, OrderResponse, OrderSummary
from app.orders.service import OrderProblem, create_order, order_response

router = APIRouter(prefix="/orders", tags=["orders"])


def require_customer(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "customer":
        raise HTTPException(403, "Customer access required")
    return user


@router.get("", response_model=list[OrderSummary])
def list_orders(
    user: Annotated[User, Depends(require_customer)],
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> list[Order]:
    return list(session.scalars(select(Order).where(Order.customer_id == user.id)
                               .order_by(Order.id.desc()).limit(limit).offset(offset)))


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: Annotated[int, Path(ge=1, le=2147483647)],
    user: Annotated[User, Depends(require_customer)],
    session: Annotated[Session, Depends(get_session)],
) -> OrderResponse:
    order = session.scalar(select(Order).where(Order.id == order_id, Order.customer_id == user.id))
    if order is None:
        raise HTTPException(404, "Order not found")
    return order_response(session, order)


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
