# Промт: создать Telegram-бот для управления VPN-подписками (3x-ui)

## Контекст

Нужно создать Telegram-бота на Python для управления VPN-клиентами через панель **3x-ui**.
Бот — личный инструмент одного администратора. Он позволяет создавать VPN-клиентов,
смотреть статистику, продлевать подписки и управлять серверами — всё из Telegram,
без захода в веб-панель.

**Перед началом замени следующие данные на свои:**

```
BOT_TOKEN=<токен от @BotFather>
ADMIN_ID=<твой Telegram user_id>
SUB_BASE_URL=<базовый URL подписочного сервера, напр. https://sub.example.com:8888/sub>
```

---

## Стек

- Python 3.9+
- `aiogram==3.x` (asyncio Telegram bot framework)
- `aiosqlite` (асинхронная SQLite БД)
- `aiohttp` (HTTP-клиент к 3x-ui)
- `python-dotenv`
- Деплой: **Docker Compose**

---

## Структура проекта

```
bot/
├── main.py
├── config.py
├── database.py
├── xui_client.py
├── link_builder.py
├── calendar_widget.py
├── handlers/
│   ├── __init__.py
│   ├── start.py
│   ├── create_user.py
│   ├── stats.py
│   └── admin.py
├── .env
├── Dockerfile
├── docker-compose.yml
└── data/           ← папка для bot.db (создаётся автоматически)
```

---

## main.py

- Создаёт `Bot`, `Dispatcher(storage=MemoryStorage())`
- Регистрирует `AdminOnlyMiddleware` — middleware, которая молча игнорирует ВСЕ апдейты
  от пользователей, чей `user.id != ADMIN_ID`. Никаких ответов, просто `return`.
- Подключает все роутеры: start, create_user, stats, admin
- Инициализирует БД при старте
- `await dp.start_polling(bot, skip_updates=True)`

---

## config.py

```python
import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DB_PATH = os.getenv("DB_PATH", "./data/bot.db")
SUB_BASE_URL = os.getenv("SUB_BASE_URL")  # напр. https://sub.example.com:8888/sub
```

---

## database.py — две таблицы

### Таблица `servers`

| Поле | Тип | Описание |
|---|---|---|
| id | INTEGER PK | авто |
| key | TEXT UNIQUE | уникальный ключ сервера, напр. `cz` |
| button_name | TEXT | текст кнопки в боте, напр. `🇨🇿 Чехия` |
| country_flag | TEXT | эмодзи флага, напр. `🇨🇿` |
| url | TEXT | URL панели 3x-ui, напр. `https://panel.example.com:2053` |
| username | TEXT | логин к панели |
| password | TEXT | пароль к панели |
| inbound_id | INTEGER | ID инбаунда по умолчанию |
| is_active | BOOLEAN | 1 = активен |

### Таблица `settings`

Ключ-значение. Дефолтные значения при инициализации:

| Ключ | Значение по умолчанию | Описание |
|---|---|---|
| app_name | Happ | Название VPN-приложения |
| app_link_ios | https://apps.apple.com/us/app/happ-proxy-utility/id6504287215 | Ссылка App Store |
| app_link_android | https://play.google.com/store/apps/details?id=com.happproxy | Ссылка Google Play |
| default_username | admin | Логин для всех панелей (используется при добавлении сервера) |
| default_password | changeme | Пароль для всех панелей |
| last_server_key | (пусто) | Последний использованный сервер (авто-выбор) |

Функции: `init_db()`, `get_all_servers()`, `get_server(key)`, `add_server(...)`,
`deactivate_server(key)`, `get_setting(key)`, `set_setting(key, value)`, `get_all_settings()`

---

## xui_client.py — HTTP-клиент к 3x-ui

Класс `XUIClient(url, username, password)`.

**Важно:** Использует cookie-сессию (`aiohttp.ClientSession`). Сессия открывается при `login()`,
закрывается при `logout()`. Всегда вызывай `logout()` в `finally`.

### Методы и эндпоинты

```python
async def login() -> bool
    # POST /login, json={"username": ..., "password": ...}
    # Создаёт self._session

async def logout()
    # GET /logout, закрывает сессию

async def get_inbound_info(inbound_id: int) -> Optional[dict]
    # GET /panel/api/inbounds/get/{inbound_id}

async def get_inbounds_list() -> list
    # GET /panel/api/inbounds/list

async def get_all_clients(inbound_id: int) -> list
    # Через get_inbound_info, парсит settings JSON → clients[]

async def create_client(inbound_id, email, note, traffic_bytes, expiry_ms) -> Optional[dict]
    # POST /panel/api/inbounds/addClient
    # ВАЖНО: settings передаётся как json.dumps({"clients": [...]}) — строка, не dict!
    # Возвращает {"uuid": ..., "email": ...}

async def update_client_expiry(inbound_id, client_uuid, client_dict, new_expiry_ms) -> bool
    # POST /panel/api/inbounds/updateClient/{client_uuid}
    # payload: {"id": inbound_id, "settings": json.dumps({"clients": [{**client_dict, "expiryTime": new_expiry_ms}]})}

async def delete_client(inbound_id, uuid) -> bool
    # POST /panel/api/inbounds/{inbound_id}/delClient/{uuid}

async def get_client_stats(email) -> Optional[dict]
    # GET /panel/api/inbounds/getClientTraffics/{email}
    # Возвращает {"up": bytes, "down": bytes, ...}

async def get_online_clients() -> list
    # POST /panel/api/inbounds/onlines
    # Возвращает список email онлайн-клиентов

async def get_server_status() -> Optional[dict]
    # GET /server/status

async def restart_xray() -> bool
    # POST /server/restartXrayService
```

### Структура payload для create_client / update_client:

```python
import json, uuid

client_uuid = str(uuid.uuid4())
payload = {
    "id": inbound_id,
    "settings": json.dumps({   # ← json.dumps! НЕ dict напрямую
        "clients": [{
            "id": client_uuid,
            "email": email,
            "limitIp": 0,
            "totalGB": traffic_bytes,   # bytes, 0 = безлимит
            "expiryTime": expiry_ms,    # unix ms, 0 = бессрочно
            "enable": True,
            "tgId": "",
            "subId": "",
            "comment": note,
        }]
    }),
}
```

---

## handlers/start.py

### Главное меню (ReplyKeyboardMarkup, resize_keyboard=True):

```
➕ Новый  |  📊 Стат
🔄 Xray   |  🖥 Серверы
```

Функция `admin_keyboard()` возвращает эту клавиатуру.

`/start` — показывает меню (только для ADMIN_ID).
`/cancel` и тексты `"❌ Отмена"`, `"🔙 Назад"` — очищают FSM и показывают меню.

**Важно:** При отправке пустого текста с клавиатурой Telegram иногда отклоняет.
Используй `·` (средняя точка U+00B7) как минимальный текст вместо пустой строки.

---

## handlers/create_user.py — FSM создания клиента

### Состояния (StatesGroup `CreateUser`):

1. **SelectServer** — выбор сервера
2. **SelectInbound** — выбор инбаунда (если их > 1)
3. **EnterNick** — ввод ника
4. **EnterNote** — примечание
5. **SelectTraffic** — выбор трафика
6. **SelectExpiry** — выбор срока
7. **EnterCustomDate** — инлайн-календарь
8. **Confirm** — подтверждение

### Шаг 1: SelectServer

ReplyKeyboard: по одной кнопке на каждый сервер (button_name) + `❌ Отмена`.
При выборе сервера — запросить список инбаундов через `get_inbounds_list()`:
- 0 инбаундов → использовать `server["inbound_id"]`, перейти к EnterNick
- 1 инбаунд → выбрать автоматически, перейти к EnterNick
- 2+ инбаунда → показать список, перейти к SelectInbound

### Шаг 2: SelectInbound (если нужен)

ReplyKeyboard: список инбаундов по `remark` + `🔙 Назад`.

### Шаг 3: EnterNick

Свободный ввод. `🔙 Назад` → вернуться к выбору инбаунда или сервера.

### Шаг 4: EnterNote

Кнопки: `🔙 Назад` | `➡️ Пропустить`. Свободный ввод.

### Шаг 5: SelectTraffic

Кнопки: `1 GB` | `1000 GB` | `🔙 Назад`

### Шаг 6: SelectExpiry

Кнопки: `3 дня` | `+1 год` | `📅 Выбрать дату` | `🔙 Назад`

Маппинг:
- `3 дня` → сегодня + 3 дня
- `+1 год` → сегодня + 1 год

### Шаг 7: EnterCustomDate (если выбрали дату)

Инлайн-календарь. Реализуй отдельно в `calendar_widget.py`.
Callback-данные: `cal:prev:YYYY:MM`, `cal:next:YYYY:MM`, `cal:select:YYYY:MM:DD`, `cal:cancel`, `cal:ignore`.

### Шаг 8: Confirm

Показывает карточку с данными:
```
📋 Проверь данные:

Сервер:      🇨🇿 Чехия
Инбаунд:     WhiteList  (если выбирался)
Ник:         Андрей
Примечание:  другу
Трафик:      1000 GB
До:          30.03.2027 (365 дней)
Профиль:     Андрей_cz🇨🇿
```

Inline-кнопки подтверждения:
```
✅ Выполнить  |  ❌ Отмена
    ✏️ Редактировать
```

Кнопка `✏️ Редактировать` показывает меню выбора поля:
```
👤 Ник      |  📝 Примечание
📦 Трафик   |  📅 Срок
      ↩️ Назад
```
После редактирования поля → возврат на экран подтверждения.

### Имя профиля / email

```python
server_suffix = f"_{server['key']}{server['country_flag']}"
email = nick.replace(" ", "_") + server_suffix
# Пример: "andrey_cz🇨🇿"
```

### Финальное сообщение (после создания)

Формат Markdown, предпросмотр ссылок отключён (`LinkPreviewOptions(is_disabled=True)`):

```
👋 Привет, {nick}! Это твой лучший ВПН, действуй:

1️⃣ Скачай **{app_name}**, если его нет:
[🍎 App Store]({app_link_ios})
[▶️ Google Play]({app_link_android})

2️⃣ Тапни по блоку ниже — ссылка скопируется:
```{SUB_BASE_URL}/{uuid}```

3️⃣ Теперь открой **{app_name}** и вставь скопированное из буфера через + справа вверху
```

Ссылка — подписочная (`{SUB_BASE_URL}/{uuid}`), **не vless://**. Это важно.
После отправки — запомнить `last_server_key` в settings, очистить FSM.

---

## handlers/stats.py — статистика

### Вход (кнопка 📊 Стат)

Inline-список серверов + кнопка `🧪 Тест серверов` в начале + `❌ Отмена`.

### Меню сервера

```
📋 Все пользователи  |  🖥 Статус
    ➕ Новый пользователь
         🔙 Назад
```

### 📋 Все пользователи

Собирает клиентов со **всех инбаундов** сервера (через `get_inbounds_list()`, парсит settings каждого).
Показывает список inline-кнопок, по 2 в ряд:
- `{статус} {email}` → callback: `stats:card:{server_key}:{inbound_id}:{email}`

Статусы:
- 🔴 — срок истёк
- 🟡 — < 7 дней до истечения ИЛИ трафик > 90%
- ✅ — онлайн прямо сейчас
- 🟢 — активен

### Карточка клиента (stats:card)

Текст:
```
{статус} {email}
📦 {использовано MB}
📅 {MM.YY} · {N дн.}   (если > 300 дней — только MM.YY)
```

Inline-кнопки:
```
🔗 RELAY WL  |  🔗 RELAY RU
ПРОДЛИТЬ     |  🗑 Удалить
```

**RELAY WL** (`stats:sublink:{server_key}:{inbound_id}:{email}`):
→ находит uuid клиента, отправляет `<pre>{SUB_BASE_URL}/{uuid}</pre>` (HTML parse_mode)

**RELAY RU** (`stats:router:{client_uuid}`):
→ скачивает подписку через aiohttp, декодирует base64, извлекает строки `vless://`,
отправляет каждую в `<pre>...</pre>` (HTML)

**ПРОДЛИТЬ** (`stats:extend:{server_key}:{inbound_id}:{email}`):
→ находит клиента, берёт его `expiryTime`
→ если ещё активен (expiryTime > today): новая дата = expiryTime + 1 год
→ если истёк: новая дата = сегодня + 1 год
→ вызывает `update_client_expiry()`
→ отвечает: `✅ {email} продлён до {DD.MM.YYYY}`

**Удалить** — двойное подтверждение → `delete_client(inbound_id, uuid)`

### 🧪 Тест серверов (stats:test)

Проверяет все серверы **параллельно** (`asyncio.gather`).
Для каждого: логинится, считает клиентов, онлайн, пинг.
Показывает сводку:
```
🟢 Название · N польз. · онлайн: M · Xms
🔴 Название · недоступен
━━━━━━━━━━━━━━
Серверов онлайн: X/Y
Всего подключений: N
Онлайн сейчас: M
```
Если есть 🔴 — кнопка `🔄 Перезапустить упавшие (N)` → рестарт Xray параллельно,
затем кнопка `🔁 Повторить тест`.

### 🖥 Статус сервера

Показывает: панель онлайн/офлайн, Xray Running/Stopped, uptime, CPU%, RAM, пинг.

---

## handlers/admin.py — управление серверами (кнопка 🖥 Серверы)

Inline-меню:
```
➕ Добавить  |  📋 Список
❌ Удалить   |  🔄 Перезагрузить Xray
   📋 Клонировать инбаунд
```

### ➕ Добавить сервер (FSM AddServer)

Шаги ввода:
1. Ключ (короткий, напр. `cz`)
2. Название кнопки (напр. `🇨🇿 Чехия`)
3. Флаг-эмодзи (напр. `🇨🇿`)
4. URL панели (напр. `https://panel.example.com:2053`)
5. ID инбаунда (число)

Логин/пароль **не спрашиваются** — берутся из `settings.default_username` / `settings.default_password`.

### ❌ Удалить сервер

Выбор из списка → подтверждение → `deactivate_server(key)` (не физическое удаление, is_active = 0).

### 🔄 Перезагрузить Xray

Одна кнопка → рестарт **всех** серверов параллельно → отчёт ✅/❌ по каждому.

### 📋 Клонировать инбаунд

Выбрать сервер → выбрать инбаунд → ввести название → ввести порт → создать копию инбаунда
через `/panel/api/inbounds/add`, clients очищаются (пустой инбаунд).

---

## Технические нюансы (критически важно)

1. **settings в API — строка, не dict:**
   ```python
   "settings": json.dumps({"clients": [...]})  # ← всегда json.dumps!
   ```

2. **parse_mode HTML везде где есть vless://-ссылки** (содержат `_` которые ломают Markdown):
   ```python
   await message.answer(f"<pre>{link}</pre>", parse_mode="HTML")
   ```

3. **Минимальный текст для ReplyKeyboard:** используй `·` (U+00B7), не пустую строку и не `\u200b`.

4. **Callback-данные с email:** email может содержать `:`, поэтому split делать с `maxsplit`:
   ```python
   parts = call.data.split(":", 4)  # "stats:card:server_key:inbound_id:email"
   ```

5. **expiryTime в миллисекундах:**
   ```python
   expiry_ms = int(datetime(year, month, day, 23, 59, 59).timestamp() * 1000)
   ```

6. **Автовыбор последнего сервера:** при входе в create_user проверяй `settings.last_server_key`,
   если совпадает с существующим сервером — ставь его первым в списке или выбирай автоматически.

---

## Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### docker-compose.yml

```yaml
services:
  bot:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
```

### requirements.txt

```
aiogram>=3.4.0
aiosqlite
aiohttp
python-dotenv
```

---

## Что нужно заменить на свои данные

| Что | Где |
|---|---|
| BOT_TOKEN | .env |
| ADMIN_ID | .env |
| SUB_BASE_URL | .env (базовый URL подписочного сервера) |
| default_username / default_password | .env или через бота в settings |
| app_name, app_link_ios, app_link_android | через settings в БД или задать дефолты в database.py |

---

## Деплой

```bash
# Первый раз
git clone <repo>
cd <repo>
cp .env.example .env
# заполнить .env
mkdir data
docker compose up -d --build

# Обновление
git pull && docker compose build && docker compose up -d
```
