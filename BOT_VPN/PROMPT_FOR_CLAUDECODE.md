# XUI-BOT — Промпт для Claude Code

Ты работаешь как оркестратор агентов. Выполняй задачи строго последовательно.
Не жди подтверждения между агентами. После каждого агента выводи: ✅ Агент N завершён.

Рабочая папка: ~/xui-bot
Создай если нет: mkdir -p ~/xui-bot && cd ~/xui-bot

Технологии: Python 3.11, aiogram 3.x, aiosqlite, aiohttp, python-dotenv

---

═══════════════════════════════════════
АГЕНТ 1 — Project Setup
Создаёт скелет: папки, пустые файлы, зависимости
═══════════════════════════════════════

```bash
mkdir -p ~/xui-bot/handlers ~/xui-bot/data
cd ~/xui-bot
touch main.py config.py xui_client.py database.py link_builder.py calendar_widget.py
touch handlers/__init__.py handlers/start.py handlers/create_user.py
touch handlers/stats.py handlers/admin.py handlers/admin_settings.py
```

Создай requirements.txt:
```
aiogram==3.13.0
aiosqlite==0.20.0
aiohttp==3.10.0
python-dotenv==1.0.1
```

Создай .env.example:
```
BOT_TOKEN=
ADMIN_ID=
DB_PATH=./data/bot.db
```

Создай .gitignore:
```
.env
data/
__pycache__/
*.pyc
*.log
.DS_Store
```

✅ Агент 1 завершён

---

═══════════════════════════════════════
АГЕНТ 2 — Database
Пишет database.py — вся работа с SQLite
═══════════════════════════════════════

Файл: ~/xui-bot/database.py. Использовать aiosqlite.

Таблица servers:
```sql
CREATE TABLE IF NOT EXISTS servers (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  key          TEXT UNIQUE NOT NULL,
  button_name  TEXT NOT NULL,
  country_flag TEXT NOT NULL,
  url          TEXT NOT NULL,
  username     TEXT NOT NULL,
  password     TEXT NOT NULL,
  inbound_id   INTEGER NOT NULL,
  is_active    BOOLEAN DEFAULT 1
);
```

Таблица settings (key-value):
```sql
CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

Начальные значения (INSERT OR IGNORE в init_db):
```
profile_prefix   → ''
profile_postfix  → ''
message_footer   → 'Вставь ссылку в приложение Happ'
app_name         → 'Happ'
app_link_ios     → 'https://apps.apple.com/us/app/happ-proxy-utility/id6504287215'
app_link_android → 'https://play.google.com/store/apps/details?id=com.happproxy'
```

Методы:
- init_db()
- get_all_servers() → list[dict]
- get_server(key) → dict | None
- add_server(key, button_name, country_flag, url, username, password, inbound_id)
- deactivate_server(key)
- server_exists(key) → bool
- get_setting(key) → str
- set_setting(key, value)
- get_all_settings() → dict

✅ Агент 2 завершён

---

═══════════════════════════════════════
АГЕНТ 3 — XUI Client
Пишет xui_client.py — HTTP-диалог с 3x-ui API
═══════════════════════════════════════

Файл: ~/xui-bot/xui_client.py
Класс XUIClient(url, username, password).
Авторизация через сессионные cookies (не токены Bearer).
Timeout 10 секунд. Использовать aiohttp.ClientSession.

Методы:
```
login() → bool
logout()
test_connection() → bool              # login + ping + logout
get_inbound_info(inbound_id) → dict   # GET /panel/api/inbounds/get/{id}
create_client(inbound_id, email, note, traffic_bytes, expiry_ms) → dict
  # POST /panel/api/inbounds/addClient
  # traffic_bytes=0 → безлимит, expiry_ms=0 → бессрочно
get_all_clients(inbound_id) → list    # clientStats из inbound
get_client_stats(email) → dict        # GET /panel/api/inbounds/getClientTraffics/{email}
get_server_status() → dict            # GET /server/status
restart_xray() → bool                 # POST /server/restartXrayService
```

Все методы в try/except. При ошибке — логировать, возвращать None/False.

✅ Агент 3 завершён

---

═══════════════════════════════════════
АГЕНТ 4 — Link Builder
Пишет link_builder.py — сборка прямого URI для клиентов
═══════════════════════════════════════

Файл: ~/xui-bot/link_builder.py

Функция: build_link(inbound_info, client_uuid, client_password, profile_name) → str

Имя профиля: {prefix}{ник}{postfix}{flag}  →  VIP_Иванов_2026🇵🇱

Протоколы:

VLESS:
vless://{uuid}@{host}:{port}?type={network}&security={security}&...#{profile_name}
Reality параметры: pbk, fp, sni, sid, spx, flow=xtls-rprx-vision
WS параметры: path, host header

VMESS:
vmess://{base64(json)}
json: {v,ps,add,port,id,aid,scy,net,type,host,path,tls,sni}

TROJAN:
trojan://{password}@{host}:{port}?security={security}&sni={sni}#{profile_name}

Host брать из streamSettings, fallback — из URL панели.

✅ Агент 4 завершён

---

═══════════════════════════════════════
АГЕНТ 5 — Calendar Widget
Пишет calendar_widget.py — инлайн-календарь выбора даты
═══════════════════════════════════════

Файл: ~/xui-bot/calendar_widget.py. Для aiogram 3.x.

Callback data: cal:{action}:{year}:{month}:{day}
Actions: day, prev, next, quick_1m, quick_3m, quick_6m, quick_1y, ignore

Функции:
- create_calendar(year, month) → InlineKeyboardMarkup
  Месяц с числами, кнопки ◀️ ▶️. Прошедшие дни → cal:ignore:0:0:0
- create_quick_buttons() → InlineKeyboardMarkup
  Ряд: +1 мес | +3 мес | +6 мес | +1 год
- process_calendar_selection(data) → date | None

Минимальная дата — завтра.

✅ Агент 5 завершён

---

═══════════════════════════════════════
АГЕНТ 6 — Config + Main
Пишет config.py и main.py — точка входа
═══════════════════════════════════════

config.py:
- Загрузка .env через python-dotenv
- Экспорт: BOT_TOKEN (str), ADMIN_ID (int), DB_PATH (str)

main.py:
- Инициализация Bot и Dispatcher (aiogram 3.x)
- Подключение всех роутеров из handlers/
- database.init_db() при старте
- Логирование в bot.log (RotatingFileHandler 5MB, 3 backup)
- asyncio.run(main())

✅ Агент 6 завершён

---

═══════════════════════════════════════
АГЕНТ 7 — Handler: Start
Пишет handlers/start.py — главное меню, роли, /cancel
═══════════════════════════════════════

Файл: ~/xui-bot/handlers/start.py

/start если user.id == ADMIN_ID:
```
[➕ Создать пользователя] [📊 Статистика         ]
[🔄 Перезагрузить Xray ] [⚙️ Управление серверами]
[        ⚙️ Настройки профиля         ]
```

/start если обычный пользователь:
- Кнопки серверов из get_all_servers() по button_name
- Если серверов нет: "Серверы пока не добавлены"

/cancel:
- Сбросить FSM
- "Действие отменено ❌"

✅ Агент 7 завершён

---

═══════════════════════════════════════
АГЕНТ 8 — Handler: Create User
Пишет handlers/create_user.py — FSM создания VPN-профиля
Самый сложный хендлер: 7 шагов, использует агентов 3, 4, 5
═══════════════════════════════════════

Файл: ~/xui-bot/handlers/create_user.py

FSM States:
SelectServer → EnterNick → EnterNote → SelectTraffic →
SelectExpiry → EnterCustomDate → Confirm

Шаг 1 SelectServer:
Кнопки серверов из БД + ❌ Отмена

Шаг 2 EnterNick:
Текстом. Кнопка 🔙 Назад.

Шаг 3 EnterNote:
Текстом. Кнопки: 🔙 Назад | ➡️ Пропустить

Шаг 4 SelectTraffic:
10 GB | 30 GB | 50 GB | 100 GB | ♾ Безлимит
Кнопка 🔙 Назад.

Шаг 5 SelectExpiry:
+1 мес | +3 мес | +6 мес | +1 год | 📅 Выбрать дату
При "📅 Выбрать дату" → state EnterCustomDate → calendar_widget.
Кнопка 🔙 Назад.

Шаг 6 Confirm — preview:
```
📋 Проверь данные:

Сервер:      🇵🇱 Польша-1
Ник:         Иванов
Примечание:  Друг
Трафик:      50 GB
До:          18.03.2027 (365 дней)
Профиль:     VIP_Иванов_2026🇵🇱

✅ Выполнить    ❌ Отмена
```

После ✅ Выполнить:
1. XUIClient.login()
2. get_inbound_info(inbound_id)
3. create_client(inbound_id, email, note, traffic_bytes, expiry_ms)
4. get_all_settings() → prefix, postfix, flag, app_name, links
5. build_link(inbound_info, uuid, profile_name)
6. Отправить сообщение в ТОЧНО таком формате:

```
✅ Пользователь создан!

👋 Привет! Это твой новый VPN-профиль.

📋 Скопируй ссылку ниже:
```
vless://...полная ссылка...
```

📱 Вставь ссылку в приложение **{app_name}**

⬇️ Скачать:
[App Store (iOS)]({app_link_ios}) · [Google Play (Android)]({app_link_android})
```

КРИТИЧНО: ссылка ВСЕГДА в блоке тройных обратных кавычек.
Telegram автоматически показывает кнопку копирования.
Текст и ссылки брать из settings — не хардкодить.

✅ Агент 8 завершён

---

═══════════════════════════════════════
АГЕНТ 9 — Handler: Stats
Пишет handlers/stats.py — статистика пользователей и серверов
═══════════════════════════════════════

Файл: ~/xui-bot/handlers/stats.py

"📊 Статистика" → выбор сервера → меню:
📋 Все пользователи | 👤 Найти пользователя | 🖥 Статус сервера

"📋 Все пользователи":
get_all_clients(inbound_id), форматировать каждого:
🟢 активен / 🟡 заканчивается (<7 дней или >90% трафика) / 🔴 истёк
⚠️ если трафик >90%

"👤 Найти пользователя":
Ввести ник → искать на ВСЕХ серверах через asyncio.gather → карточка:
```
👤 Иванов
Сервер:       🇵🇱 Польша-1
Использовано: 23.4 GB / 50 GB
Осталось:     26.6 GB
До:           18.03.2027 (364 дня)
Примечание:   Друг
Статус:       🟢 Активен
```

"🖥 Статус сервера":
get_server_status(), пинг через время login():
```
🖥 Польша-1
Панель:  🟢 Онлайн
Xray:    🟢 Запущен
Uptime:  14 дней 6 часов
Версия:  Xray 1.8.x
CPU:     12%
RAM:     1.2 GB / 4 GB
Пинг:    42ms
```

✅ Агент 9 завершён

---

═══════════════════════════════════════
АГЕНТ 10 — Handler: Admin
Пишет handlers/admin.py — управление серверами + перезагрузка Xray
═══════════════════════════════════════

Файл: ~/xui-bot/handlers/admin.py

"⚙️ Управление серверами" → меню:
➕ Добавить | 📋 Список | ❌ Удалить | 🔄 Перезагрузить Xray

"➕ Добавить сервер" (FSM AKey→AName→AFlag→AUrl→ALogin→APassword→AInbound):
1. Ключ (латиница, пример: poland_3)
2. Название кнопки (пример: 🇵🇱 Польша-3)
3. Эмодзи флага (пример: 🇵🇱)
4. URL панели (пример: https://pl3.domain.com:2053)
5. Логин
6. Пароль
7. Inbound ID (число)
→ test_connection():
  ✅ add_server() → "Сервер добавлен!"
  ❌ "Не удалось подключиться" + 🔄 Повторить | ❌ Отмена
На каждом шаге кнопка 🔙 Назад.

"📋 Список серверов": button_name, url, inbound_id, статус.

"❌ Удалить": кнопки → подтверждение → deactivate_server()

"🔄 Перезагрузить Xray":
Шаг 1: выбор сервера
Шаг 2 — первое предупреждение:
```
⚠️ Перезагрузка Xray на 🇵🇱 Польша-1
Соединения прервутся на 3–5 секунд.
✅ Продолжить    ❌ Отмена
```
Шаг 3 — второе предупреждение:
```
🔴 Последнее предупреждение!
Точно перезагрузить Xray на 🇵🇱 Польша-1?
🔄 ДА, ПЕРЕЗАГРУЗИТЬ    ❌ Отмена
```
После: restart_xray() → "✅ Xray перезагружен. 🕐 {время}"

✅ Агент 10 завершён

---

═══════════════════════════════════════
АГЕНТ 11 — Handler: Admin Settings
Пишет handlers/admin_settings.py — редактирование настроек
═══════════════════════════════════════

Файл: ~/xui-bot/handlers/admin_settings.py

"⚙️ Настройки профиля" → текущие значения + кнопки ✏️:
```
Префикс:           VIP_              [✏️]
Постфикс:          _2026             [✏️]
Текст под ссылкой: Вставь в Happ     [✏️]
Приложение:        Happ              [✏️]
Ссылка iOS:        apps.apple.com/.. [✏️]
Ссылка Android:    play.google.com/. [✏️]
```

Каждая кнопка ✏️ → FSM: ввести новое значение → set_setting() → обновить меню.

✅ Агент 11 завершён

---

═══════════════════════════════════════
АГЕНТ 12 — Docker + README
Пишет Dockerfile, docker-compose.yml, README.md
═══════════════════════════════════════

Dockerfile:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data
CMD ["python", "main.py"]
```

docker-compose.yml:
```yaml
version: '3.8'
services:
  bot:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./bot.log:/app/bot.log
```

README.md — инструкция по запуску:
1. Создать бота @BotFather → BOT_TOKEN
2. Узнать Telegram ID у @userinfobot → ADMIN_ID
3. git clone, cp .env.example .env, заполнить .env
4. docker-compose up -d
5. Написать /start в боте
6. Добавить первый сервер через ⚙️ Управление серверами
7. Обновление: git pull && docker-compose restart

✅ Агент 12 завершён

---

═══════════════════════════════════════
АГЕНТ 13 — GitHub: создать репо и запушить
Устанавливает gh CLI, создаёт приватный репозиторий, пушит код
═══════════════════════════════════════

Шаг 1 — установить GitHub CLI если нет:
```bash
# Проверить:
gh --version

# Если нет, установить:
# macOS:
brew install gh

# Linux (Ubuntu/Debian):
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
  https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh -y
```

Шаг 2 — авторизоваться в GitHub (откроет браузер):
```bash
gh auth login
# Выбрать: GitHub.com → HTTPS → Login with a web browser
```

Шаг 3 — инициализировать git:
```bash
cd ~/xui-bot
git init
git add .
git commit -m "Initial commit: xui-bot — Telegram bot for 3x-ui VPN management"
```

Шаг 4 — создать приватный репо и запушить одной командой:
```bash
gh repo create xui-bot --private --source=. --remote=origin --push
```

Шаг 5 — проверить что .env и data/ не попали в коммит:
```bash
git show --stat HEAD | grep -E "\.env$|^data/"
# Если что-то нашлось — это ошибка, нужно исправить
```

Шаг 6 — показать ссылку на репозиторий:
```bash
gh repo view | grep "https://github.com"
```

✅ Агент 13 завершён — код на GitHub!

---

═══════════════════════════════════════
ФИНАЛЬНЫЙ ОТЧЁТ
═══════════════════════════════════════

Вывести:

✅ xui-bot готов и опубликован на GitHub

Создано файлов: 14
Агентов выполнено: 13

Следующие шаги для запуска на VPS:
1. git clone {URL репозитория}
2. cd xui-bot && cp .env.example .env
3. Заполнить .env: BOT_TOKEN и ADMIN_ID
4. docker-compose up -d
5. Написать /start боту в Telegram
6. Добавить серверы через ⚙️ Управление серверами
