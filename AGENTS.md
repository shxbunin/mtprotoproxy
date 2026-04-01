# AGENTS.md

## Purpose

This repository is now a small MTProto subscription platform built around three runtime services:

- `bot`: Telegram bot on `aiogram`;
- `sync`: PostgreSQL -> active proxy users exporter;
- `proxy`: working copy of `mtprotoproxy` with config reload wrapper.

The original upstream project snapshot is preserved in `.source/` and must be treated as read-only reference material.

## Non-Negotiable Rules

- Do not modify files inside `.source/`.
- Do not import Python code from `.source/`.
- If behavior from the old project is needed, reimplement or copy it into the working codebase explicitly.
- Treat `proxy/mtprotoproxy.py` and `proxy/pyaes/` as protocol-sensitive code.
- Prefer small changes in `app/` and avoid unnecessary edits to MTProto handshake logic.

## Repository Map

- `.source/`: untouched snapshot of the original project.
- `app/`: bot, SQLAlchemy models, repositories, services, sync worker.
- `proxy/`: live proxy service, copied from the original project and wrapped for runtime config reload.
- `docker-compose.yml`: orchestrates `db`, `bot`, `sync`, `proxy`.
- `.env.example`: deployment template.
- `README.md`: server build and deployment guide.

## Runtime Architecture

### `bot`

- Entry point: `app/mtproxy_manager/bot/main.py`
- Stack: `aiogram`
- Responsibility:
  - handles `/start`;
  - shows plan selection buttons (`1 month`, `3 months`, `1 year`);
  - creates or extends subscription in PostgreSQL;
  - sends a `tg://proxy` link through a `Подключить` button.

### `sync`

- Entry point: `app/mtproxy_manager/sync/main.py`
- Responsibility:
  - reads active subscriptions from PostgreSQL;
  - writes active proxy users into the shared runtime file;
  - excludes expired users automatically.

### `proxy`

- Entry points:
  - `proxy/run_proxy.py`
  - `proxy/mtprotoproxy.py`
- Responsibility:
  - runs the copied MTProto proxy;
  - loads users from the generated runtime file through `proxy/config.py`;
  - reloads config when the runtime file changes.

## Data Flow

1. User sends `/start`.
2. Bot shows subscription plans.
3. User chooses a plan.
4. Bot creates or extends subscription and stores expiry in PostgreSQL.
5. Bot responds with a `Подключить` button containing the `tg://proxy` link.
6. `sync` exports only active users to `PROXY_ACTIVE_USERS_FILE`.
7. `proxy/run_proxy.py` watches the file and reloads the proxy.
8. After expiry, the user disappears from the exported user set and the proxy stops accepting that secret.

## App Structure

Inside `app/mtproxy_manager/`:

- `core/`: settings and logging.
- `db/`: SQLAlchemy base, models, session factory.
- `repositories/`: database access.
- `services/`: subscription activation, link building, active-user export.
- `shared/`: plan definitions, time helpers, Telegram identity DTO.
- `bot/`: aiogram handlers, keyboards, callback payloads.
- `sync/`: export worker.

Keep files focused and short. Prefer pushing business logic into `services/` and database access into `repositories/`.

## Database Model

Current persistence is intentionally simple:

- `telegram_users`: Telegram identity, permanent MTProto secret, current subscription expiry.
- `subscriptions`: historical activation records.

If a user buys another plan before expiration, the new period starts from the current expiry, not from "now".

## Proxy Rules

- `proxy/config.py` is the adapter layer between environment variables and `mtprotoproxy`.
- Active users come from `PROXY_ACTIVE_USERS_FILE`, not from static code.
- Prefer changing `proxy/config.py` or `proxy/run_proxy.py` instead of patching protocol code.
- Only edit `proxy/mtprotoproxy.py` when absolutely necessary.
- If you must change protocol code, preserve handshake layout and existing anti-detection behavior.

## Risky Areas

Highest risk:

- `proxy/mtprotoproxy.py`
- `proxy/pyaes/`
- `proxy/config.py` when changing how users or modes are loaded
- `proxy/run_proxy.py` when changing reload behavior

Medium risk:

- subscription activation logic in `app/mtproxy_manager/services/subscriptions.py`
- export logic in `app/mtproxy_manager/services/export.py`
- proxy link generation in `app/mtproxy_manager/services/proxy_links.py`

Lower risk:

- bot texts and keyboards;
- README updates;
- Docker packaging changes.

## Editing Guidelines

- Keep application logic out of handlers when possible.
- Keep SQLAlchemy queries inside repositories or clearly scoped services.
- Do not add long monolithic files if a helper or service keeps the structure cleaner.
- Preserve the separation between bot logic, DB logic, export logic, and proxy runtime logic.
- For subscription expiry behavior, keep it silent unless the user explicitly asks for notifications.
- Prefer environment-driven configuration over hardcoded deployment values.

## Deployment Notes

- Deployment is expected through Docker Compose.
- `db` uses the official Postgres image.
- `bot` and `sync` use separate Dockerfiles, even though they share the same application package.
- `proxy` is a separate service and should stay operationally independent from bot internals.

## Verification

After non-trivial changes, verify at least:

- Python syntax with `python -m compileall app proxy`;
- `/start` plan selection flow;
- generated `tg://proxy` link format for the active proxy mode;
- active user export file updates;
- proxy reload after runtime file changes;
- expired subscriptions disappearing from the exported users set.
