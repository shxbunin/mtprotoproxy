from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from mtproxy_manager.bot.keyboards.subscriptions import build_connect_keyboard
from mtproxy_manager.core.config import get_settings
from mtproxy_manager.db.session import get_session_factory
from mtproxy_manager.repositories.users import TelegramUserRepository
from mtproxy_manager.services.proxy_links import ProxyLinkService
from mtproxy_manager.services.subscriptions import SubscriptionService
from mtproxy_manager.shared.telegram import TelegramIdentity
from mtproxy_manager.shared.time import format_utc_datetime, utc_now

router = Router()

DEFAULT_PLAN_CODE = "3m"


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    if message.from_user is None:
        return

    settings = get_settings()
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        user = await TelegramUserRepository(session).get_by_telegram_id(message.from_user.id)
        has_active_subscription = (
            user is not None
            and user.subscription_expires_at is not None
            and user.subscription_expires_at > utc_now()
        )

        if has_active_subscription:
            user.username = message.from_user.username
            user.first_name = message.from_user.first_name
            user.last_name = message.from_user.last_name
            await session.commit()
        else:
            result = await SubscriptionService(session).activate(
                identity=TelegramIdentity(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                ),
                plan_code=DEFAULT_PLAN_CODE,
            )
            user = result.user

    link = ProxyLinkService(settings).build_link(user.proxy_secret)
    expires_at = format_utc_datetime(user.subscription_expires_at)
    intro = (
        "Ваша текущая подписка MTProto Proxy"
        if has_active_subscription
        else "Конфиг MTProto Proxy на <b>3 месяца</b>"
    )
    await message.answer(
        (
            f"{intro} активен до <b>{expires_at}</b>.\n"
            "Нажмите кнопку ниже, чтобы подключить прокси в Telegram."
        ),
        reply_markup=build_connect_keyboard(link),
    )
