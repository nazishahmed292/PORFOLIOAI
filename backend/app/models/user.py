"""Accounts. Only the portfolio owner logs in; visitors are anonymous."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import UserRole
from app.models.column_types import enum_type

if TYPE_CHECKING:
    from app.models.profile import Profile


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # Emails are stored lowercase so the unique index is effectively case-insensitive
        # (PostgreSQL unique indexes are case-sensitive). Services normalise before insert.
        CheckConstraint("email = lower(email)", name="email_lowercase"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    # bcrypt/argon2 hash (Phase 3). The plain password is never stored.
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(
        enum_type(UserRole, "user_role"), default=UserRole.ADMIN, server_default=UserRole.ADMIN.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True, uselist=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
