from sqlalchemy import CheckConstraint, Index, String, Text, func
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
