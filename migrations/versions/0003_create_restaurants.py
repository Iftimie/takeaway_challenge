"""Create restaurants.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "restaurants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.String(1000), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_restaurants"),
    )


def downgrade() -> None:
    op.drop_table("restaurants")
