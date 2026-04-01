# MTProto Proxy Bot

Проект разворачивает три основных сервиса:

- `bot`: Telegram-бот на `aiogram`, который по `/start` показывает выбор подписки и отдает кнопку `Подключить` с `tg://proxy`-ссылкой;
- `sync`: фоновый сервис, который читает активные подписки из PostgreSQL и выгружает активные MTProto-секреты в runtime-файл;
- `proxy`: отдельный экземпляр `mtprotoproxy`, который читает только активных пользователей и автоматически перезагружает конфиг при изменениях.

Оригинальный проект прокси сохранен в `.source/`. Он используется только как reference snapshot. Рабочая копия прокси лежит в `proxy/`.

## Структура

- `.source/`: исходный снимок оригинального проекта, не трогаем и не импортируем.
- `app/`: бот, SQLAlchemy-модели, сервисы подписок и синхронизации.
- `proxy/`: рабочая копия `mtprotoproxy` и обвязка для runtime reload.
- `docker-compose.yml`: запуск `db`, `bot`, `sync`, `proxy`.

## Как это работает

1. Пользователь отправляет `/start` боту.
2. Бот показывает inline-кнопки: `1 месяц`, `3 месяца`, `1 год`.
3. После выбора бот создает или продлевает подписку в PostgreSQL.
4. Для пользователя хранится постоянный MTProto secret.
5. Бот отправляет сообщение с кнопкой `Подключить` и `tg://proxy` ссылкой.
6. Сервис `sync` периодически выбирает только активные подписки и записывает их в `/runtime/active_users.json`.
7. Сервис `proxy` замечает изменение файла и отправляет `SIGUSR2` дочернему `mtprotoproxy`, чтобы тот перечитал `proxy/config.py`.
8. После истечения срока подписки пользователь автоматически исчезает из runtime-конфига, и прокси перестает принимать его secret.

Никаких уведомлений об окончании подписки не отправляется.

## Быстрый запуск на сервере

Ниже пример для Ubuntu/Debian-сервера.

### 1. Установить Docker и Compose

Если Docker еще не установлен:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

После добавления пользователя в группу `docker` лучше перелогиниться.

Проверьте установку:

```bash
docker --version
docker compose version
```

### 2. Склонировать проект

```bash
git clone <your-repository-url>
cd mtprotoproxy
```

### 3. Подготовить `.env`

Скопируйте шаблон:

```bash
cp .env.example .env
```

Заполните минимум эти переменные:

- `BOT_TOKEN`: токен бота из `@BotFather`.
- `POSTGRES_PASSWORD`: пароль для PostgreSQL.
- `PROXY_PUBLIC_HOST`: IP или домен сервера, который увидит пользователь в `tg://proxy` ссылке.
- `PROXY_PORT`: внешний порт прокси, обычно `443`.
- `PROXY_MODE`: `tls`, `secure` или `classic`. Для большинства случаев лучше `tls`.
- `PROXY_TLS_DOMAIN`: домен для TLS-режима. Лучше указать реальный существующий домен.

Пример:

```env
BOT_TOKEN=1234567890:replace_me
POSTGRES_DB=mtproxy
POSTGRES_USER=mtproxy
POSTGRES_PASSWORD=strong-password
DB_HOST=db
DB_PORT=5432

PROXY_PUBLIC_HOST=203.0.113.10
PROXY_PORT=443
PROXY_MODE=tls
PROXY_TLS_DOMAIN=www.cloudflare.com
PROXY_MASK=true
PROXY_MASK_HOST=www.cloudflare.com
PROXY_MASK_PORT=443
PROXY_USE_MIDDLE_PROXY=false
PROXY_AD_TAG=
PROXY_FAST_MODE=true
PROXY_PREFER_IPV6=false
PROXY_PROTOCOL=false
PROXY_LISTEN_ADDR_IPV4=0.0.0.0
PROXY_LISTEN_ADDR_IPV6=::
PROXY_STATS_PRINT_PERIOD=600
PROXY_METRICS_PORT=
PROXY_METRICS_WHITELIST=127.0.0.1,::1

PROXY_ACTIVE_USERS_FILE=/runtime/active_users.json
EXPORT_INTERVAL_SECONDS=60
PROXY_WATCH_INTERVAL_SECONDS=5
```

### 4. Открыть порт на сервере

Если используете `ufw`:

```bash
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
```

Если меняете `PROXY_PORT`, откройте именно его.

### 5. Собрать и запустить сервисы

```bash
docker compose up --build -d
```

Проверить статус:

```bash
docker compose ps
```

Посмотреть логи:

```bash
docker compose logs -f bot
docker compose logs -f sync
docker compose logs -f proxy
```

### 6. Проверить работу

1. Откройте бота в Telegram.
2. Отправьте `/start`.
3. Выберите срок подписки.
4. Нажмите `Подключить`.
5. Telegram должен предложить добавить прокси.

## Переменные окружения

### Бот и БД

- `BOT_TOKEN`: токен Telegram-бота.
- `POSTGRES_DB`: имя базы.
- `POSTGRES_USER`: пользователь базы.
- `POSTGRES_PASSWORD`: пароль базы.
- `DB_HOST`: адрес PostgreSQL внутри Docker Compose, по умолчанию `db`.
- `DB_PORT`: порт PostgreSQL, по умолчанию `5432`.

### Прокси и ссылки

- `PROXY_PUBLIC_HOST`: адрес сервера, который попадет в ссылку для пользователей.
- `PROXY_PORT`: порт прокси.
- `PROXY_MODE`: `classic`, `secure` или `tls`.
- `PROXY_TLS_DOMAIN`: нужен для `tls` режима.
- `PROXY_MASK`: включать ли masking для плохих клиентов.
- `PROXY_MASK_HOST`: хост, на который будут уходить bad clients. Если пусто, берется `PROXY_TLS_DOMAIN`.
- `PROXY_MASK_PORT`: порт для `MASK_HOST`.
- `PROXY_USE_MIDDLE_PROXY`: включать ли middle proxy режим.
- `PROXY_AD_TAG`: ad tag от `@MTProxybot`, если нужен advertising.
- `PROXY_FAST_MODE`: оставляет fast mode включенным для direct path.
- `PROXY_PREFER_IPV6`: предпочитать ли IPv6.
- `PROXY_PROTOCOL`: требовать ли PROXY protocol v1/v2 на входе.

### Runtime синхронизация

- `PROXY_ACTIVE_USERS_FILE`: путь к shared runtime-файлу с активными пользователями.
- `EXPORT_INTERVAL_SECONDS`: как часто сервис `sync` пересобирает runtime-файл.
- `PROXY_WATCH_INTERVAL_SECONDS`: как часто `proxy/run_proxy.py` проверяет изменение runtime-файла.

## Команды обслуживания

Остановить все сервисы:

```bash
docker compose down
```

Остановить с удалением томов:

```bash
docker compose down -v
```

Пересобрать после изменений:

```bash
docker compose up --build -d
```

Подключиться к PostgreSQL:

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## Модель данных

В PostgreSQL хранятся:

- Telegram-пользователь;
- его постоянный proxy secret;
- дата окончания текущей подписки;
- история всех активаций подписки.

Если пользователь повторно выбирает тариф до окончания действующей подписки, новая подписка продлевает текущую, а не перезаписывает ее с текущего момента.

## Важно

- Оригинальный код прокси сохранен в `.source/` и не используется напрямую в приложении.
- Рабочий прокси берется из `proxy/`.
- После истечения `subscription_expires_at` пользователь автоматически исключается из runtime-конфига.
- Бот не отправляет сообщение об окончании подписки.
- Для production лучше использовать реальный домен в `PROXY_TLS_DOMAIN` и корректно настроенный `PROXY_MASK_HOST`.
