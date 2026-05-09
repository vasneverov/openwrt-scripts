# Prompt for Claude Code — Deploy Analyst Bot

Скопируй этот файл и вставь его содержимое в Claude Code на новом компьютере.

---

## Задача

Разверни Telegram-бота **"Аналитик дня"** на VPS для нового пользователя.

Репозиторий: **https://github.com/vasneverov/claude-bot**

Сделай форк этого репозитория на GitHub аккаунт нового пользователя, затем разверни его на VPS.

---

## Что это за бот

Это **однодневный голосовой аналитик**. Не второй мозг, не база знаний — он живёт один день.

Пользователь весь день надиктовывает голосовые заметки: встречи, точки аренды, стройматериалы, домашние дела — всё вперемешку. Бот просто записывает и ждёт.

В конце дня пользователь говорит: **"сделай Excel по аренде"** — и получает аккуратную таблицу только по этой теме. Потом: **"файл по стройке"** — ещё один файл. И так по каждой теме.

Нажимает **🆕 НОВОЕ** — бот всё забывает и готов к новому дню. Файлы при этом остаются в папках, их можно скачать через кнопку **📂 ПРОЕКТЫ** или отправить себе в избранное.

---

## Что нужно от пользователя (спроси перед началом)

1. **Telegram Bot Token** — создать через [@BotFather](https://t.me/BotFather)
2. **Deepgram API Key** — зарегистрироваться на [deepgram.com](https://deepgram.com) (есть бесплатный тариф)
3. **Доступ к VPS** — IP, пользователь, пароль или SSH-ключ
4. **GitHub аккаунт** — для форка репозитория
5. **Claude Code CLI** должен быть установлен и авторизован на VPS через `claude auth login`

---

## Шаги деплоя

### 1. Форк репозитория

Попроси пользователя зайти на https://github.com/vasneverov/claude-bot и нажать **Fork** — создать копию в своём GitHub аккаунте.

Или сделай это через GitHub CLI:
```bash
gh repo fork vasneverov/claude-bot --clone=false
```

### 2. Подключись к VPS и создай пользователя

```bash
ssh root@VPS_IP

# Создаём отдельного пользователя для бота
adduser analyst
usermod -aG sudo analyst

# Переключаемся
su - analyst
```

### 3. Установи Claude Code CLI (если нет)

```bash
npm install -g @anthropic-ai/claude-code
claude auth login
# Открой ссылку в браузере и авторизуйся
```

### 4. Клонируй форк и установи зависимости

```bash
cd ~
git clone https://github.com/НОВЫЙ_ЮЗЕР/claude-bot.git
cd claude-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Создай .env файл

```bash
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=вставь_токен_от_botfather
DEEPGRAM_API_KEY=вставь_deepgram_ключ
EOF
```

### 6. Создай директории

```bash
mkdir -p storage/daily storage/projects logs
```

### 7. Настрой systemd сервис

```bash
sudo nano /etc/systemd/system/analyst-bot.service
```

Содержимое (замени `analyst` на имя своего пользователя если другое):

```ini
[Unit]
Description=Analyst Claude Bot
After=network.target

[Service]
Type=simple
User=analyst
WorkingDirectory=/home/analyst/claude-bot
ExecStart=/home/analyst/claude-bot/venv/bin/python main.py
Restart=always
RestartSec=10
EnvironmentFile=/home/analyst/claude-bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable analyst-bot
sudo systemctl start analyst-bot

# Проверить что запустился
sudo systemctl status analyst-bot
sudo journalctl -u analyst-bot -f
```

---

## Проверка работы

Отправь боту голосовое сообщение → должен ответить:
```
🎤 [14:30] текст заметки

✅ Записал. Заметок за сегодня: 1
```

Затем напиши текстом: `сделай Excel по [любая тема]` → бот должен вернуть `.xlsx` файл.

---

## Как пользоваться ботом (объясни пользователю)

**В течение дня:**
- Надиктовывай голосовые — бот записывает всё с временно́й меткой
- Говори вперемешку: аренда, встречи, покупки, дела — не важно
- Бот просто копит и ждёт

**В конце дня:**
- `"сделай Excel по аренде"` — таблица по всем точкам аренды
- `"сделай файл по стройке"` — Markdown или Excel по стройматериалам
- `"саммари по встречам"` — структурированный отчёт по встречам
- Падежи понимает: "по аренде", "по стройке", "по встречам" ✓

**Кнопки:**
- **🆕 НОВОЕ** — сбросить день, начать заново (файлы остаются)
- **📂 ПРОЕКТЫ** — скачать готовые файлы

**Файлы:**
- Хранятся в папках по дате: `storage/projects/2026-03-18/аренда.xlsx`
- Можно скачать через кнопку ПРОЕКТЫ и отправить себе в Telegram Избранное

---

## Если что-то не работает

```bash
# Посмотреть логи
sudo journalctl -u analyst-bot -n 50 --no-pager

# Перезапустить
sudo systemctl restart analyst-bot

# Проверить авторизацию Claude
su - analyst -c "claude auth status"
```

---

*Репозиторий: https://github.com/vasneverov/claude-bot*
