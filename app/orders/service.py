import hashlib
import json
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MenuItem, Order, OrderItem, Restaurant, User
from app.orders.schemas import OrderCreate, OrderLineResponse, OrderResponse


class OrderProblem(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def request_fingerprint(data: OrderCreate) -> str:
    normalized = data.model_dump()
    # The order of cart lines does not change the purchase.
    normalized["items"] = sorted(normalized["items"], key=lambda item: item["menu_item_id"])
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def order_response(session: Session, order: Order, lines: list[OrderItem] | None = None) -> OrderResponse:
    if lines is None:
        lines = list(session.scalars(select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.menu_item_id)))
    return OrderResponse(
        id=order.id, restaurant_id=order.restaurant_id,
        delivery_name=order.delivery_name, delivery_address=order.delivery_address,
        status=order.status, total=order.total, currency=order.currency,
        created_at=order.created_at,
        items=[OrderLineResponse.model_validate(line) for line in lines],
    )


def create_order(
    session: Session, customer_id: int, key: str, data: OrderCreate,
) -> tuple[OrderResponse, bool]:
    fingerprint = request_fingerprint(data)
    try:
        # Serialize this customer's requests before checking the idempotency key.
        # Refresh the role even if authentication already loaded this User.
        customer = session.scalar(select(User).where(User.id == customer_id)
                                  .with_for_update().execution_options(populate_existing=True))
        if customer is None or customer.role != "customer":
            raise OrderProblem(403, "Customer access required")
        existing = session.scalar(select(Order).where(
            Order.customer_id == customer_id, Order.idempotency_key == key,
        ))
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise OrderProblem(409, "Idempotency key already used for a different request")
            response = order_response(session, existing)
            session.commit()
            return response, False

        if session.get(Restaurant, data.restaurant_id) is None:
            raise OrderProblem(404, "Restaurant not found")
        quantities = {line.menu_item_id: line.quantity for line in data.items}
        # Consistent lock order avoids deadlocks between overlapping carts.
        items = list(session.scalars(select(MenuItem).where(
            MenuItem.id.in_(quantities), MenuItem.restaurant_id == data.restaurant_id,
        ).order_by(MenuItem.id).with_for_update()))
        if len(items) != len(quantities):
            raise OrderProblem(422, "Every menu item must exist in the selected restaurant")
        if any(not item.available for item in items):
            raise OrderProblem(409, "A menu item is unavailable")
        total = sum((item.price * quantities[item.id] for item in items), Decimal("0.00"))
        order = Order(
            customer_id=customer_id, restaurant_id=data.restaurant_id,
            delivery_name=data.delivery_name, delivery_address=data.delivery_address,
            status="pending", total=total, currency="EUR",
            idempotency_key=key, request_fingerprint=fingerprint,
        )
        session.add(order)
        session.flush()
        session.add_all([OrderItem(
            order_id=order.id, menu_item_id=item.id, name=item.name,
            unit_price=item.price, quantity=quantities[item.id],
        ) for item in items])
        session.flush()
        response = order_response(session, order)
        session.commit()
        return response, True
    except Exception:
        # Includes unexpected write failures: no partial order or reserved key.
        session.rollback()
        raise
