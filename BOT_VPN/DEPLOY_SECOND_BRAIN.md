# Задача: развернуть бота Agent Second Brain на VPS

Ты — Claude Code. Твоя задача — полностью развернуть Telegram-бота "Второй мозг" на этом VPS-сервере.

Бот транскрибирует голосовые сообщения через Deepgram, классифицирует их с помощью Claude и сохраняет заметки в Obsidian-vault. Всё работает 24/7 как systemd-сервис.

> ⚠️ **Todoist в этой установке отключён.** Интеграция с Todoist не используется — нужно удалить её из кода перед запуском (инструкции ниже в шаге 6а).

---

## Что тебе нужно сделать (по порядку)

### 1. Запроси API-ключи у пользователя

Прежде чем что-то делать, попроси у пользователя следующие данные:

- **Telegram Bot Token** — создаётся через [@BotFather](https://t.me/BotFather) командой `/newbot`
- **Telegram User ID** — можно узнать через [@userinfobot](https://t.me/userinfobot)
- **Deepgram API Key** — на [console.deepgram.com](https://console.deepgram.com/) (есть бесплатный кредит $200)
- **GitHub username** — для форка репозитория

Todoist **не нужен** — интеграция отключается на шаге 6а.

Запиши ответы — они понадобятся для `.env`.

---

### 2. Проверь и установи зависимости

Выполни в терминале:

```bash
# Проверь ОС (нужна Ubuntu 22.04+)
lsb_release -a

# Обнови систему
sudo apt update && sudo apt upgrade -y

# Установи базовые инструменты
sudo apt install -y git curl wget build-essential

# Python 3.12
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# uv (менеджер пакетов Python)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Node.js 20 (нужен для Claude Code CLI)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Claude Code CLI
npm install -g @anthropic-ai/claude-code
```

Проверь что всё установилось:

```bash
python3.12 --version   # должно быть 3.12.x
uv --version
node --version         # должно быть 20.x
claude --version
```

---

### 3. Авторизуй Claude Code

```bash
claude auth login
```

Откроется URL — скопируй его, открой в браузере, войди в аккаунт Anthropic и авторизуй доступ. Вернись в терминал — увидишь подтверждение.

---

### 4. Сделай форк репозитория и склонируй

Попроси пользователя:
1. Зайти на https://github.com/vasneverov/sbrain
2. Нажать кнопку **Fork** (вверху справа)
3. В настройках форка сделать репо **приватным** (Settings → Danger Zone → Make private) — там будут личные данные

Затем на сервере:

```bash
mkdir -p ~/projects
cd ~/projects

# Замени YOUR_GITHUB_USERNAME на реальный юзернейм пользователя
git clone https://github.com/YOUR_GITHUB_USERNAME/sbrain.git
cd sbrain

ls -la  # убедись что файлы есть
```

---

### 5. Установи зависимости проекта

```bash
cd ~/projects/sbrain
uv sync

# Проверка
uv run python -c "import aiogram; print('OK')"
```

---

### 6. Создай `.env` файл

```bash
cd ~/projects/sbrain
cp .env.example .env
nano .env
```

Заполни файл — **без Todoist**:

```env
TELEGRAM_BOT_TOKEN=<токен от BotFather>
DEEPGRAM_API_KEY=<ключ от Deepgram>
TODOIST_API_KEY=
VAULT_PATH=./vault
ALLOWED_USER_IDS=[<Telegram User ID пользователя>]
```

`TODOIST_API_KEY` оставь **пустым** (строка нужна, удалять нельзя — Python читает файл).

Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`.

---

### 6а. Отключи Todoist из кода ⚠️

Это важный шаг. В `setup.sh` есть жёсткая валидация токена Todoist — без неё скрипт упадёт с ошибкой, даже если значение пустое. Кроме того, агент-скилл `todoist-ai` пытается обращаться к Todoist при обработке. Нужно его нейтрализовать.

**Шаг 1: Найди, где в коде упоминается Todoist**

```bash
cd ~/projects/sbrain
grep -r "todoist" --include="*.py" -l
grep -r "todoist" --include="*.md" -l
grep -r "TODOIST" --include="*.py" -l
```

**Шаг 2: Найди и закомментируй код, который падает при пустом токене**

Открой каждый найденный файл и найди места, где `TODOIST_API_KEY` читается и используется для реальных запросов. Закомментируй блоки инициализации Todoist-клиента. Пример того, что нужно найти и закомментировать:

```python
# ДО:
todoist_client = TodoistAPI(os.getenv("TODOIST_API_KEY"))

# ПОСЛЕ:
# todoist_client = TodoistAPI(os.getenv("TODOIST_API_KEY"))  # disabled
todoist_client = None
```

**Шаг 3: Найди скилл `todoist-ai` и заглуши его**

```bash
find ~/projects/sbrain/.claude -name "*.md" | xargs grep -l -i "todoist" 2>/dev/null
```

Если найдёшь — открой файл и добавь в начало:

```markdown
> ⚠️ DISABLED: Todoist integration is not configured on this instance. Skip all Todoist-related actions silently.
```

**Шаг 4: Убедись что бот запускается без ошибок**

```bash
cd ~/projects/sbrain
uv run python -m d_brain
```

Если видишь `ImportError` или ошибку связанную с Todoist — скажи мне, я исправлю.

---

### 7. Очисти vault от примеров

```bash
cd ~/projects/sbrain

rm -rf vault/daily/*
rm -rf vault/thoughts/ideas/*
rm -rf vault/thoughts/learnings/*
rm -rf vault/thoughts/reflections/*
rm -rf vault/summaries/*
rm -rf vault/attachments/*

# Оставь шаблоны целей — их надо будет заполнить
ls vault/goals/
```

---

### 8. Заполни личные данные в vault

> ⚠️ **Пропусти этот шаг при первом запуске.** Не нужно заполнять файлы целей и `about.md` вручную сейчас. Пользователь сам наполнит свой профиль голосом уже после того, как бот заработает — просто отправив голосовое сообщение с рассказом о себе, целях и приоритетах. Бот всё сохранит в нужные места сам.

Файлы для будущего самостоятельного редактирования (если понадобится):

```
vault/goals/0-vision-3y.md          # 3-летнее видение
vault/goals/1-yearly-2026.md        # цели на год
vault/goals/2-monthly.md            # приоритеты на месяц
vault/goals/3-weekly.md             # фокус на неделю
vault/.claude/skills/dbrain-processor/references/about.md  # профиль пользователя
```

---

### 9. Тестовый запуск

```bash
cd ~/projects/sbrain
uv run python -m d_brain
```

Должно появиться:
```
INFO:aiogram.dispatcher:Start polling
INFO:aiogram.dispatcher:Run polling for bot @имя_бота
```

Зайди в Telegram, найди своего бота, отправь `/start`, потом голосовое сообщение. Если всё работает — жми `Ctrl+C` и идём дальше.

---

### 10. Настрой systemd-сервис (автозапуск)

Замени `YOUR_USERNAME` на реального пользователя сервера (`whoami`).

```bash
# Узнай имя пользователя
whoami
```

Создай сервис:

```bash
sudo nano /etc/systemd/system/d-brain-bot.service
```

Вставь (замени `YOUR_USERNAME`):

```ini
[Unit]
Description=d-brain Telegram Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/projects/sbrain
ExecStart=/home/YOUR_USERNAME/.local/bin/uv run python -m d_brain
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Запусти и включи автостарт:

```bash
sudo systemctl daemon-reload
sudo systemctl start d-brain-bot
sudo systemctl enable d-brain-bot

# Проверь статус
sudo systemctl status d-brain-bot
```

Статус должен быть `active (running)`.

---

### 11. Настрой ежедневную обработку (21:00)

```bash
# Сделай скрипт исполняемым
chmod +x ~/projects/sbrain/scripts/process.sh

# Отредактируй пути в скрипте (замени YOUR_USERNAME)
nano ~/projects/sbrain/scripts/process.sh
```

В начале файла найди и замени пути:
```bash
export HOME="/home/YOUR_USERNAME"
PROJECT_DIR="/home/YOUR_USERNAME/projects/sbrain"
```

Создай timer:

```bash
sudo nano /etc/systemd/system/d-brain-process.timer
```

```ini
[Unit]
Description=Run d-brain processing daily at 21:00

[Timer]
OnCalendar=*-*-* 21:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Создай сервис для timer:

```bash
sudo nano /etc/systemd/system/d-brain-process.service
```

```ini
[Unit]
Description=d-brain Daily Processing

[Service]
Type=oneshot
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/projects/sbrain
ExecStart=/home/YOUR_USERNAME/projects/sbrain/scripts/process.sh
Environment=PYTHONUNBUFFERED=1
```

Включи:

```bash
sudo systemctl daemon-reload
sudo systemctl enable d-brain-process.timer
sudo systemctl start d-brain-process.timer

# Проверь
sudo systemctl list-timers | grep d-brain
```

---

### 12. Финальная проверка

```bash
# Статус всех сервисов
sudo systemctl status 'd-brain-*'

# Живые логи бота
sudo journalctl -u d-brain-bot -f
```

---

## Полезные команды на каждый день

```bash
# Перезапустить бота
sudo systemctl restart d-brain-bot

# Посмотреть последние логи
sudo journalctl -u d-brain-bot -n 100

# Запустить обработку вручную прямо сейчас
cd ~/projects/sbrain && ./scripts/process.sh

# Обновить код из GitHub
cd ~/projects/sbrain
git pull
uv sync
sudo systemctl restart d-brain-bot
```

---

## Если что-то пошло не так

**Бот не отвечает:**
```bash
sudo journalctl -u d-brain-bot -n 50
# Проверь токен:
grep TELEGRAM_BOT_TOKEN ~/projects/sbrain/.env
```

**Голос не транскрибируется:**
```bash
grep DEEPGRAM ~/projects/sbrain/.env
sudo journalctl -u d-brain-bot | grep -i deepgram
```

**Ошибки Claude:**
```bash
claude auth status
claude auth login  # переавторизоваться
```

**Ошибки связанные с Todoist (если появились):**
```bash
# Убедись что TODOIST_API_KEY пустой в .env:
grep TODOIST ~/projects/sbrain/.env
# Должно быть: TODOIST_API_KEY=
# Если бот всё равно падает с Todoist-ошибкой — вернись к шагу 6а
```

**Нет прав на файлы:**
```bash
sudo chown -R $USER:$USER ~/projects/sbrain
chmod -R 755 ~/projects/sbrain
```

---

## Архитектура системы (без Todoist)

```
Голосовое сообщение в Telegram
    ↓
Deepgram (транскрипция)
    ↓
Claude Code (классификация + обработка)
    ↓
Obsidian vault (заметки)
    ↓
Ежедневный отчёт в Telegram (21:00)
```

**Что хранится в vault:**
```
vault/
├── daily/          # Ежедневные записи (голос, текст, фото)
├── goals/          # Видение → год → месяц → неделя
├── business/
│   ├── crm/        # Карточки клиентов
│   └── network/    # Контакты
├── projects/       # Проекты и задачи
├── thoughts/
│   ├── ideas/      # Идеи
│   ├── learnings/  # Выводы
│   └── reflections/# Рефлексии
├── MOC/            # Карты контента (авто)
└── MEMORY.md       # Долгосрочная память агента
```

---

## Исходный репозиторий

https://github.com/vasneverov/sbrain

Документация по VPS: https://github.com/vasneverov/sbrain/blob/main/docs/vps-setup.md
