from __future__ import annotations

import html
import secrets
from dataclasses import dataclass
from datetime import datetime
import json

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from mtproxy_manager.core.config import get_settings
from mtproxy_manager.core.logging import setup_logging
from mtproxy_manager.db.session import create_database, get_session_factory
from mtproxy_manager.repositories.users import TelegramUserRepository
from mtproxy_manager.services.proxy_links import ProxyLinkService
from mtproxy_manager.shared.time import format_utc_datetime, utc_now

settings = get_settings()
app = FastAPI(title="MTProto Admin")
security = HTTPBasic()


@dataclass(frozen=True)
class DashboardRow:
    telegram_id: int
    username: str
    config_link: str
    proxy_secret: str
    last_online_at: datetime | None
    expires_at: datetime | None
    is_active: bool


def _load_last_seen() -> dict[str, datetime]:
    try:
        payload = json.loads(settings.proxy_last_seen_file_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

    users = payload.get("users", {})
    if not isinstance(users, dict):
        return {}

    result: dict[str, datetime] = {}
    for user, value in users.items():
        if not isinstance(user, str) or not isinstance(value, str):
            continue
        try:
            result[user] = datetime.fromisoformat(value)
        except ValueError:
            continue
    return result


async def _fetch_rows(session: AsyncSession) -> list[DashboardRow]:
    last_seen = _load_last_seen()
    users = await TelegramUserRepository(session).get_all_users()
    proxy_links = ProxyLinkService(settings)
    now = utc_now()

    rows = []
    for user in users:
        username = user.username or "-"
        proxy_user = f"user_{user.telegram_id}"
        expires_at = user.subscription_expires_at
        is_active = expires_at is not None and expires_at > now
        rows.append(
            DashboardRow(
                telegram_id=user.telegram_id,
                username=username,
                config_link=proxy_links.build_link(user.proxy_secret),
                proxy_secret=user.proxy_secret,
                last_online_at=last_seen.get(proxy_user),
                expires_at=expires_at,
                is_active=is_active,
            )
        )
    return rows


def _format_optional_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"
    return format_utc_datetime(value)


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _render_table(rows: list[DashboardRow]) -> str:
    generated_at = format_utc_datetime(utc_now())
    body = []
    for row in rows:
        status = "active" if row.is_active else "expired"
        status_label = "Активна" if row.is_active else "Истекла"
        body.append(
            "".join(
                [
                    "<tr>",
                    f"<td>{row.telegram_id}</td>",
                    f"<td>{_escape(row.username)}</td>",
                    f"<td><code>{_escape(row.proxy_secret)}</code><br><a href=\"{_escape(row.config_link)}\">tg://proxy link</a></td>",
                    f"<td>{_escape(_format_optional_datetime(row.last_online_at))}</td>",
                    f"<td>{_escape(_format_optional_datetime(row.expires_at))}</td>",
                    f"<td><span class=\"badge {status}\">{status_label}</span></td>",
                    "</tr>",
                ]
            )
        )

    rows_html = "".join(body) or (
        "<tr><td colspan=\"6\" class=\"empty\">Выданных конфигов пока нет.</td></tr>"
    )
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MTProto Admin</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f3efe6;
      --panel: rgba(255, 252, 247, 0.9);
      --line: rgba(82, 59, 39, 0.14);
      --text: #2f241a;
      --muted: #6a5643;
      --accent: #a44a21;
      --accent-soft: #f6dfcf;
      --ok: #2f6a4f;
      --ok-bg: #ddefe3;
      --warn: #8a3b24;
      --warn-bg: #f8ddd4;
      --shadow: 0 22px 60px rgba(85, 58, 33, 0.14);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(255,255,255,0.7), transparent 35%),
        linear-gradient(135deg, #e8dcc8 0%, #f5f0e8 48%, #e7dfd2 100%);
      min-height: 100vh;
    }}
    .wrap {{
      width: min(1200px, calc(100% - 32px));
      margin: 32px auto;
    }}
    .hero {{
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: 28px;
      background: var(--panel);
      backdrop-filter: blur(12px);
      box-shadow: var(--shadow);
    }}
    h1 {{
      margin: 0;
      font-size: clamp(30px, 5vw, 52px);
      font-weight: 700;
      letter-spacing: -0.03em;
    }}
    .meta {{
      margin-top: 10px;
      color: var(--muted);
      font-size: 16px;
    }}
    .table-card {{
      margin-top: 20px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 28px;
      background: rgba(255, 250, 243, 0.92);
      box-shadow: var(--shadow);
    }}
    .scroll {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 920px; }}
    th, td {{ padding: 18px 20px; text-align: left; vertical-align: top; }}
    th {{
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
      background: rgba(164, 74, 33, 0.06);
    }}
    tr + tr td {{ border-top: 1px solid var(--line); }}
    td code {{
      display: inline-block;
      padding: 5px 8px;
      border-radius: 10px;
      background: rgba(82, 59, 39, 0.06);
      font-size: 13px;
      word-break: break-all;
    }}
    a {{ color: var(--accent); }}
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .badge.active {{ color: var(--ok); background: var(--ok-bg); }}
    .badge.expired {{ color: var(--warn); background: var(--warn-bg); }}
    .empty {{ text-align: center; color: var(--muted); }}
    @media (max-width: 720px) {{
      .wrap {{ width: min(100% - 16px, 100%); margin: 16px auto; }}
      .hero {{ padding: 20px; border-radius: 22px; }}
      th, td {{ padding: 14px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Issued Proxy Configs</h1>
      <div class="meta">Всего записей: {len(rows)}. Обновлено: {generated_at}.</div>
    </section>
    <section class="table-card">
      <div class="scroll">
        <table>
          <thead>
            <tr>
              <th>Telegram ID</th>
              <th>Username</th>
              <th>Config</th>
              <th>Last online</th>
              <th>Subscription ends</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
    </section>
  </div>
</body>
</html>"""


def _verify(credentials: HTTPBasicCredentials) -> None:
    username_ok = secrets.compare_digest(credentials.username, settings.admin_username)
    password_ok = secrets.compare_digest(credentials.password, settings.admin_password)
    if not username_ok or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.on_event("startup")
async def startup() -> None:
    setup_logging("admin")
    await create_database(settings)


@app.get("/", response_class=HTMLResponse)
async def dashboard(credentials: HTTPBasicCredentials = Depends(security)):
    _verify(credentials)
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        rows = await _fetch_rows(session)
    return HTMLResponse(_render_table(rows))
