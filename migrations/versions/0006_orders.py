"""Create orders and purchased item snapshots."""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("delivery_name", sa.String(200), nullable=False),
        sa.Column("delivery_address", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("total", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_orders"),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"]),
        sa.UniqueConstraint("customer_id", "idempotency_key", name="uq_orders_customer_key"),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'out_for_delivery', 'delivered')", name="ck_orders_status"),
        sa.CheckConstraint("total > 0 AND total <= 9999999999999999.99", name="ck_orders_total"),
        sa.CheckConstraint("currency = 'EUR'", name="ck_orders_currency"),
        sa.CheckConstraint("length(trim(delivery_name)) > 0 AND length(trim(delivery_address)) > 0", name="ck_orders_delivery"),
        sa.CheckConstraint("length(trim(idempotency_key)) > 0", name="ck_orders_key"),
        sa.CheckConstraint("request_fingerprint ~ '^[0-9a-f]{64}$'", name="ck_orders_fingerprint"),
    )
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_order_items"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"]),
        sa.UniqueConstraint("order_id", "menu_item_id", name="uq_order_items_menu_item"),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity"),
        sa.CheckConstraint("unit_price > 0 AND unit_price <= 99999999.99", name="ck_order_items_price"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_order_items_name"),
    )


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
