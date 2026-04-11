from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message

from mtproxy_manager.bot.keyboards.subscriptions import build_admin_keyboard, build_connect_keyboard
from mtproxy_manager.core.config import get_settings
from mtproxy_manager.db.session import get_session_factory
from mtproxy_manager.services.broadcasts import BroadcastService

router = Router()

CONFIG_ROTATION_TEXT = (
    "<b>Конфигурация прокси была обновлена.</b> Чтобы <b>работа прокси возобновилась</b>, подключите <b>новый конфиг</b> по кнопке ниже."
)


@router.message(Command("admin"))
async def handle_admin(message: Message) -> None:
    if message.from_user is None:
        return

    settings = get_settings()
    if message.from_user.id not in settings.admin_telegram_ids:
        return

    config_path = settings.admin_wireguard_config_path
    if not config_path.exists():
        await message.answer(
            "WG-конфиг еще не готов. Сначала поднимите `wireguard`, потом повторите /admin."
        )
        return

    await message.answer_document(
        FSInputFile(config_path),
        caption="WireGuard-конфиг для доступа к админке.",
    )
    await message.answer(
        "После импорта конфига подключитесь к WireGuard и откройте статистику кнопкой ниже.",
        reply_markup=build_admin_keyboard(settings.admin_stats_url),
    )


@router.message(Command("notify_config_update"))
async def handle_notify_config_update(message: Message) -> None:
    if message.from_user is None:
        return

    settings = get_settings()
    if message.from_user.id not in settings.admin_telegram_ids:
        return

    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        result = await BroadcastService(session, settings).notify_config_rotation(
            bot=message.bot,
            text=CONFIG_ROTATION_TEXT,
            reply_markup_factory=build_connect_keyboard,
        )

    await message.answer(
        (
            "Рассылка завершена. "
            f"Всего активных пользователей: {result.total}. "
            f"Доставлено: {result.delivered}. "
            f"Ошибок: {result.failed}."
        )
    )
