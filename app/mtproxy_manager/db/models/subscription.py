from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mtproxy_manager.db.base import Base
from mtproxy_manager.shared.time import utc_now

if TYPE_CHECKING:
    from mtproxy_manager.db.models.user import TelegramUser


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("telegram_users.id", ondelete="CASCADE"), index=True)
    plan_code: Mapped[str] = mapped_column(String(16), index=True)
    duration_days: Mapped[int] = mapped_column(Integer)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["TelegramUser"] = relationship("TelegramUser", back_populates="subscriptions")
