from __future__ import annotations

import asyncio
import logging

from mtproxy_manager.core.config import get_settings
from mtproxy_manager.core.logging import setup_logging
from mtproxy_manager.db.session import create_database
from mtproxy_manager.services.export import ActiveUsersExportService

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    setup_logging("sync")
    await create_database(settings)

    exporter = ActiveUsersExportService(settings)
    while True:
        result = await exporter.export()
        logger.info(
            "Active users exported: count=%s changed=%s",
            result.active_user_count,
            result.changed,
        )
        await asyncio.sleep(settings.export_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
