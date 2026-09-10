"""Enforce case-insensitive email uniqueness.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.create_index("uq_users_email", "users", [sa.text("lower(email)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_users_email", table_name="users")
    op.create_unique_constraint("uq_users_email", "users", ["email"])
