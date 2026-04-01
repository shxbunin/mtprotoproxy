from __future__ import annotations

import json
from dataclasses import dataclass

from mtproxy_manager.core.config import Settings
from mtproxy_manager.db.session import get_session_factory
from mtproxy_manager.repositories.users import TelegramUserRepository
from mtproxy_manager.shared.time import utc_now


@dataclass(frozen=True)
class ExportResult:
    active_user_count: int
    changed: bool


class ActiveUsersExportService:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def export(self) -> ExportResult:
        session_factory = get_session_factory(self._settings)
        async with session_factory() as session:
            users = await TelegramUserRepository(session).get_active_users(utc_now())

        payload = {
            "users": {f"user_{user.telegram_id}": user.proxy_secret for user in users}
        }
        changed = self._write_if_changed(payload)
        return ExportResult(active_user_count=len(payload["users"]), changed=changed)

    def _write_if_changed(self, payload: dict[str, dict[str, str]]) -> bool:
        target_path = self._settings.export_file_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=True, indent=2) + "\n"
        if target_path.exists() and target_path.read_text(encoding="utf-8") == serialized:
            return False

        temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        temp_path.write_text(serialized, encoding="utf-8")
        temp_path.replace(target_path)
        return True
