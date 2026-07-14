# User vertical onboarding preferences — vertical, language, role.

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UserVerticalPreferences(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_vertical_preferences_v1"
    __table_args__ = (
        Index("ix_user_vertical_prefs_telegram", "telegram_user_id", unique=True),
        Index("ix_user_vertical_prefs_vertical", "vertical"),
        Index("ix_user_vertical_prefs_language", "language"),
        Index("ix_user_vertical_prefs_tenant", "tenant_code"),
        Index("ix_user_vertical_prefs_source_link", "source_link"),
    )

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    vertical: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tenant_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_link: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="ru", nullable=False)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    onboarding_step: Mapped[str | None] = mapped_column(String(32), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<UserVerticalPreferences telegram={self.telegram_user_id} "
            f"vertical={self.vertical} lang={self.language}>"
        )
