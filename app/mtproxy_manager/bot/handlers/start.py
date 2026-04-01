from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from mtproxy_manager.bot.callbacks import SubscriptionPlanCallback
from mtproxy_manager.bot.keyboards.subscriptions import build_connect_keyboard, build_subscription_keyboard
from mtproxy_manager.core.config import get_settings
from mtproxy_manager.db.session import get_session_factory
from mtproxy_manager.services.proxy_links import ProxyLinkService
from mtproxy_manager.services.subscriptions import SubscriptionService
from mtproxy_manager.shared.plans import get_plan
from mtproxy_manager.shared.telegram import TelegramIdentity
from mtproxy_manager.shared.time import format_utc_datetime

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Выберите срок подписки для MTProto Proxy.",
        reply_markup=build_subscription_keyboard(),
    )


@router.callback_query(SubscriptionPlanCallback.filter())
async def handle_plan_selection(
    callback: CallbackQuery,
    callback_data: SubscriptionPlanCallback,
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    settings = get_settings()
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        result = await SubscriptionService(session).activate(
            identity=TelegramIdentity(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
            ),
            plan_code=callback_data.code,
        )

    plan = get_plan(callback_data.code)
    link = ProxyLinkService(settings).build_link(result.user.proxy_secret)
    expires_at = format_utc_datetime(result.subscription.ends_at)
    await callback.message.answer(
        (
            f"Подписка <b>{plan.title}</b> активна до <b>{expires_at}</b>.\n"
            "Нажмите кнопку ниже, чтобы подключить прокси в Telegram."
        ),
        reply_markup=build_connect_keyboard(link),
    )
    await callback.answer("Конфиг готов")
