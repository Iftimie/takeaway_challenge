"""Create menu items."""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "menu_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_menu_items"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"]),
        sa.CheckConstraint("price > 0 AND price <= 99999999.99", name="ck_menu_items_price"),
    )


def downgrade() -> None:
    op.drop_table("menu_items")
