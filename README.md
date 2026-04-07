# MTProto Proxy Bot

Проект разворачивает четыре основных сервиса:

- `bot`: Telegram-бот на `aiogram`, который по `/start` сразу выдает конфиг на 3 месяца и кнопку `Подключить` с `tg://proxy`-ссылкой;
- `bot`: Telegram-бот на `aiogram`, который по `/start` сразу выдает конфиг на 3 месяца и по `/admin` отправляет WireGuard-конфиг администраторам;
- `sync`: фоновый сервис, который читает активные подписки из PostgreSQL и выгружает активные MTProto-секреты в runtime-файл;
- `proxy`: отдельный экземпляр `mtprotoproxy`, который читает только активных пользователей, автоматически перезагружает конфиг при изменениях и пишет `last online` в runtime-файл;
- `admin`: web-панель с таблицей выданных конфигов, доступная только из внутренней Docker-сети;
- `wireguard`: VPN-контейнер, который дает доступ к `admin` без ручной установки WireGuard на сервере.

Оригинальный проект прокси сохранен в `.source/`. Он используется только как reference snapshot. Рабочая копия прокси лежит в `proxy/`.

## Структура

- `.source/`: исходный снимок оригинального проекта, не трогаем и не импортируем.
- `app/`: бот, SQLAlchemy-модели, сервисы подписок и синхронизации.
- `proxy/`: рабочая копия `mtprotoproxy` и обвязка для runtime reload.
- `docker-compose.yml`: запуск `db`, `bot`, `sync`, `proxy`, `admin`, `wireguard`.

## Как это работает

1. Пользователь отправляет `/start` боту.
2. Бот сразу создает или продлевает подписку на 3 месяца в PostgreSQL.
3. Для пользователя хранится постоянный MTProto secret.
4. Бот отправляет сообщение с кнопкой `Подключить` и `tg://proxy` ссылкой.
5. Сервис `sync` периодически выбирает только активные подписки и записывает их в `/runtime/active_users.json`.
6. Сервис `proxy` замечает изменение файла и отправляет `SIGUSR2` дочернему `mtprotoproxy`, чтобы тот перечитал `proxy/config.py`.
7. После успешного подключения через прокси `proxy` обновляет `/runtime/last_seen.json`.
8. Сервис `admin` показывает таблицу с Telegram ID, username, конфигом, последним онлайном и датой окончания подписки.
9. Сервис `wireguard` создает клиентский VPN-конфиг и дает доступ к `admin` по внутреннему адресу `http://172.29.0.10:8080`.
10. После истечения срока подписки пользователь автоматически исчезает из runtime-конфига, и прокси перестает принимать его secret.
11. Команда `/admin` работает только для Telegram ID из списка администраторов и отправляет `.conf` файл plus кнопку на статистику.

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
- `ADMIN_USERNAME`: логин для локальной admin-панели.
- `ADMIN_PASSWORD`: пароль для локальной admin-панели.
- `ADMIN_TELEGRAM_IDS`: список Telegram ID админов через запятую, которым доступна команда `/admin`.
- `WIREGUARD_PORT`: UDP-порт для WireGuard, обычно `51820`.

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
PROXY_LAST_SEEN_FILE=/runtime/last_seen.json
EXPORT_INTERVAL_SECONDS=60
PROXY_WATCH_INTERVAL_SECONDS=5

ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me-admin
ADMIN_TELEGRAM_IDS=123456789
ADMIN_STATS_URL=http://172.29.0.10:8080
ADMIN_WG_CONFIG_PATH=/wireguard/peer_admin/peer_admin.conf

TZ=UTC
WIREGUARD_PORT=51820
WIREGUARD_PEERS=admin
WIREGUARD_PEER_DNS=1.1.1.1
WIREGUARD_SUBNET=10.13.13.0
WIREGUARD_ALLOWED_IPS=10.13.13.0/24,172.29.0.0/24
WIREGUARD_PERSISTENT_KEEPALIVE=25
```

### 4. Открыть порт на сервере

Если используете `ufw`:

```bash
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw allow 51820/udp
```

Если меняете `PROXY_PORT` или `WIREGUARD_PORT`, откройте именно эти порты.

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
docker compose logs -f wireguard
docker compose logs -f admin
```

### 6. Проверить работу

1. Откройте бота в Telegram.
2. Отправьте `/start`.
3. Нажмите `Подключить`.
4. Telegram должен предложить добавить прокси.
5. После первого запуска заберите клиентский WireGuard-конфиг из `wireguard/peer_admin/peer_admin.conf`.
6. Импортируйте его в приложение WireGuard на своем устройстве.
7. Подключитесь к VPN и откройте `http://172.29.0.10:8080`.

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
- `PROXY_LAST_SEEN_FILE`: путь к shared runtime-файлу с временем последнего подключения по каждому пользователю.
- `EXPORT_INTERVAL_SECONDS`: как часто сервис `sync` пересобирает runtime-файл.
- `PROXY_WATCH_INTERVAL_SECONDS`: как часто `proxy/run_proxy.py` проверяет изменение runtime-файла.

### Admin-панель

- `ADMIN_USERNAME`: логин Basic Auth.
- `ADMIN_PASSWORD`: пароль Basic Auth.
- `ADMIN_TELEGRAM_IDS`: кому бот отвечает на `/admin`.
- `ADMIN_STATS_URL`: ссылка, которая будет открываться кнопкой из команды `/admin`.
- `ADMIN_WG_CONFIG_PATH`: путь внутри контейнера `bot` к WireGuard `.conf` файлу.

Панель не публикуется в интернет и доступна только через WireGuard по адресу `http://172.29.0.10:8080`.

### WireGuard

- `WIREGUARD_PORT`: внешний UDP-порт WireGuard.
- `WIREGUARD_PEERS`: имена peer-конфигов, которые контейнер создаст автоматически.
- `WIREGUARD_PEER_DNS`: DNS, который получит клиент.
- `WIREGUARD_SUBNET`: внутренняя VPN-подсеть WireGuard.
- `WIREGUARD_ALLOWED_IPS`: сети, которые клиент будет отправлять в VPN. По умолчанию сюда включены сама VPN-подсеть и подсеть admin-панели.
- `WIREGUARD_PERSISTENT_KEEPALIVE`: keepalive для клиентов за NAT.

Сгенерированные клиентские файлы появятся в `wireguard/peer_admin/peer_admin.conf` и `wireguard/peer_admin/peer_admin.png`.

## Команды бота

- `/start`: выдает текущий конфиг, а если активной подписки нет - создает новую на 3 месяца.
- `/admin`: для Telegram ID из `ADMIN_TELEGRAM_IDS` отправляет WireGuard-конфиг и кнопку `Открыть статистику`; для остальных пользователей бот молчит.

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
- его `tg://proxy` конфиг можно пересчитать из secret и env-настроек;
- время последнего онлайна через прокси хранится в runtime-файле `last_seen.json`;
- дата окончания текущей подписки;
- история всех активаций подписки.

Если пользователь повторно выбирает тариф до окончания действующей подписки, новая подписка продлевает текущую, а не перезаписывает ее с текущего момента.

## Важно

- Оригинальный код прокси сохранен в `.source/` и не используется напрямую в приложении.
- Рабочий прокси берется из `proxy/`.
- После истечения `subscription_expires_at` пользователь автоматически исключается из runtime-конфига.
- Бот не отправляет сообщение об окончании подписки.
- Для production лучше использовать реальный домен в `PROXY_TLS_DOMAIN` и корректно настроенный `PROXY_MASK_HOST`.
