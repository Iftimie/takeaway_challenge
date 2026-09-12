from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.auth.dependencies import require_assigned_staff
from app.models import Order, OrderItem
from app.orders.schemas import OrderResponse, OrderStatusUpdate
from app.orders.service import OrderProblem, order_response, update_order_status

from app.payload_logging import PayloadLoggingRoute

router = APIRouter(prefix="/restaurants/{restaurant_id}/orders", tags=["staff orders"],
                   dependencies=[Depends(require_assigned_staff)], route_class=PayloadLoggingRoute)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def change_order_status(
    restaurant_id: Annotated[int, Path(ge=1, le=2147483647)],
    order_id: Annotated[int, Path(ge=1, le=2147483647)],
    data: OrderStatusUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> OrderResponse:
    try:
        return update_order_status(session, restaurant_id, order_id, data.status)
    except OrderProblem as error:
        raise HTTPException(error.status_code, error.detail) from None


@router.get("", response_model=list[OrderResponse])
def list_restaurant_orders(
    restaurant_id: Annotated[int, Path(ge=1, le=2147483647)],
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> list[OrderResponse]:
    orders = list(session.scalars(select(Order).where(Order.restaurant_id == restaurant_id)
                                 .order_by(Order.id.desc()).limit(limit).offset(offset)))
    if not orders:
        return []
    # Fetch all purchased lines for this page in one query.
    lines_by_order: dict[int, list[OrderItem]] = {order.id: [] for order in orders}
    lines = session.scalars(select(OrderItem).where(OrderItem.order_id.in_(lines_by_order))
                            .order_by(OrderItem.menu_item_id))
    for line in lines:
        lines_by_order[line.order_id].append(line)
    return [order_response(session, order, lines_by_order[order.id]) for order in orders]
