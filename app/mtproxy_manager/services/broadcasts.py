from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup

from mtproxy_manager.repositories.users import TelegramUserRepository
from mtproxy_manager.services.proxy_links import ProxyLinkService
from mtproxy_manager.shared.time import utc_now

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BroadcastResult:
    total: int
    delivered: int
    failed: int


class BroadcastService:
    def __init__(self, session, settings):
        self._session = session
        self._proxy_links = ProxyLinkService(settings)

    async def notify_config_rotation(
        self,
        bot: Bot,
        text: str,
        reply_markup_factory,
    ) -> BroadcastResult:
        users = await TelegramUserRepository(self._session).get_active_users(utc_now())
        delivered = 0
        failed = 0

        for user in users:
            try:
                proxy_link = self._proxy_links.build_link(user.proxy_secret)
                reply_markup: InlineKeyboardMarkup = reply_markup_factory(proxy_link)
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    reply_markup=reply_markup,
                )
                delivered += 1
            except TelegramAPIError as exc:
                failed += 1
                logger.warning("Unable to notify user %s: %s", user.telegram_id, exc)

        return BroadcastResult(total=len(users), delivered=delivered, failed=failed)
