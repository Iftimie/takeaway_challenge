from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(Text)
    default_address: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("uq_users_email", func.lower(email), unique=True),
        CheckConstraint(
            "role IN ('customer', 'staff', 'admin')", name="ck_users_role"
        ),
    )


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(String(1000))


class StaffAssignment(Base):
    __tablename__ = "staff_assignments"

    staff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), primary_key=True)


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    name: Mapped[str] = mapped_column(String(200))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    available: Mapped[bool]

    __table_args__ = (
        CheckConstraint("price > 0 AND price <= 99999999.99", name="ck_menu_items_price"),
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    delivery_name: Mapped[str] = mapped_column(String(200))
    delivery_address: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(20))
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("customer_id", "idempotency_key", name="uq_orders_customer_key"),
        CheckConstraint("status IN ('pending', 'accepted', 'out_for_delivery', 'delivered')", name="ck_orders_status"),
        CheckConstraint("total > 0 AND total <= 9999999999999999.99", name="ck_orders_total"),
        CheckConstraint("currency = 'EUR'", name="ck_orders_currency"),
        CheckConstraint("length(trim(delivery_name)) > 0 AND length(trim(delivery_address)) > 0", name="ck_orders_delivery"),
        CheckConstraint("length(trim(idempotency_key)) > 0", name="ck_orders_key"),
        CheckConstraint("request_fingerprint ~ '^[0-9a-f]{64}$'", name="ck_orders_fingerprint"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    name: Mapped[str] = mapped_column(String(200))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int]

    __table_args__ = (
        UniqueConstraint("order_id", "menu_item_id", name="uq_order_items_menu_item"),
        CheckConstraint("quantity > 0", name="ck_order_items_quantity"),
        CheckConstraint("unit_price > 0 AND unit_price <= 99999999.99", name="ck_order_items_price"),
        CheckConstraint("length(trim(name)) > 0", name="ck_order_items_name"),
    )
