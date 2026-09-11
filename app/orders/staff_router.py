from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.auth.dependencies import require_assigned_staff
from app.models import Order, OrderItem
from app.orders.schemas import OrderResponse
from app.orders.service import order_response

router = APIRouter(prefix="/restaurants/{restaurant_id}/orders", tags=["staff orders"],
                   dependencies=[Depends(require_assigned_staff)])


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
