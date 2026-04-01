from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from mtproxy_manager.db.models.subscription import Subscription


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, subscription: Subscription) -> None:
        self._session.add(subscription)
