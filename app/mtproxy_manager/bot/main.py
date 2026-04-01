from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from mtproxy_manager.bot.handlers.start import router as start_router
from mtproxy_manager.core.config import get_settings
from mtproxy_manager.core.logging import setup_logging
from mtproxy_manager.db.session import create_database


async def main() -> None:
    settings = get_settings()
    setup_logging("bot")
    await create_database(settings)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(start_router)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
