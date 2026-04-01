from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from mtproxy_manager.db.models.subscription import Subscription
from mtproxy_manager.db.models.user import TelegramUser
from mtproxy_manager.repositories.subscriptions import SubscriptionRepository
from mtproxy_manager.repositories.users import TelegramUserRepository
from mtproxy_manager.services.secrets import generate_proxy_secret
from mtproxy_manager.shared.plans import get_plan
from mtproxy_manager.shared.telegram import TelegramIdentity
from mtproxy_manager.shared.time import utc_now


@dataclass(frozen=True)
class ActivationResult:
    user: TelegramUser
    subscription: Subscription


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._users = TelegramUserRepository(session)
        self._subscriptions = SubscriptionRepository(session)

    async def activate(self, identity: TelegramIdentity, plan_code: str) -> ActivationResult:
        plan = get_plan(plan_code)
        now = utc_now()

        user = await self._users.get_by_telegram_id(identity.telegram_id)
        if user is None:
            user = TelegramUser(
                telegram_id=identity.telegram_id,
                username=identity.username,
                first_name=identity.first_name,
                last_name=identity.last_name,
                proxy_secret=generate_proxy_secret(),
            )
            self._session.add(user)
            await self._session.flush()
        else:
            user.username = identity.username
            user.first_name = identity.first_name
            user.last_name = identity.last_name

        starts_at = self._get_subscription_start(user, now)
        ends_at = starts_at + timedelta(days=plan.duration_days)
        user.subscription_expires_at = ends_at

        subscription = Subscription(
            user_id=user.id,
            plan_code=plan.code,
            duration_days=plan.duration_days,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        await self._subscriptions.add(subscription)

        await self._session.commit()
        await self._session.refresh(user)
        return ActivationResult(user=user, subscription=subscription)

    @staticmethod
    def _get_subscription_start(user: TelegramUser, now):
        if user.subscription_expires_at and user.subscription_expires_at > now:
            return user.subscription_expires_at
        return now
