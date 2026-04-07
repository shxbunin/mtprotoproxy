from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message

from mtproxy_manager.bot.keyboards.subscriptions import build_admin_keyboard
from mtproxy_manager.core.config import get_settings

router = Router()


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
