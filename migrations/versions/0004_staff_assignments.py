"""Create staff assignments."""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff_assignments",
        sa.Column("staff_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["staff_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"]),
        sa.PrimaryKeyConstraint("staff_id", "restaurant_id", name="pk_staff_assignments"),
    )


def downgrade() -> None:
    op.drop_table("staff_assignments")
