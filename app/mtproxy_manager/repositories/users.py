from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mtproxy_manager.db.models.user import TelegramUser


class TelegramUserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> TelegramUser | None:
        result = await self._session.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_active_users(self, now: datetime) -> Sequence[TelegramUser]:
        result = await self._session.execute(
            select(TelegramUser)
            .where(TelegramUser.subscription_expires_at.is_not(None))
            .where(TelegramUser.subscription_expires_at > now)
            .order_by(TelegramUser.telegram_id.asc())
        )
        return result.scalars().all()

    async def get_all_users(self) -> Sequence[TelegramUser]:
        result = await self._session.execute(
            select(TelegramUser).order_by(TelegramUser.subscription_expires_at.desc().nullslast(), TelegramUser.telegram_id.asc())
        )
        return result.scalars().all()
