# Задача: очистить vault от чужих личных данных

Ты — Claude Code. На этом сервере развёрнут бот Agent Second Brain, но в его хранилище (`vault/`) находятся **чужие личные данные** — заметки, цели, CRM-карточки и память другого человека, которые попали сюда через форк репозитория.

Твоя задача: **полностью очистить vault от чужого контента**, сохранив при этом всю структуру папок, технические файлы и конфигурацию бота. После очистки бот должен работать, но начинать с чистого листа — только для нового пользователя.

> ⚠️ Не трогай: `.env`, `src/`, `pyproject.toml`, `uv.lock`, `setup.sh`, `bootstrap.sh`, `mcp-config.json`, папки `.claude/` внутри `vault/` (там скиллы агента, не данные), `scripts/`, `deploy/`, `.github/`.

---

## Шаг 1: Останови бота

```bash
sudo systemctl stop d-brain-bot
```

Убедись что остановлен:
```bash
sudo systemctl status d-brain-bot
```

---

## Шаг 2: Найди где лежит проект

```bash
ls ~/projects/
```

Скорее всего это `~/projects/sbrain` или `~/projects/agent-second-brain`. Дальше используй правильный путь.

```bash
PROJECT_DIR=~/projects/sbrain   # или agent-second-brain
cd $PROJECT_DIR
```

---

## Шаг 3: Покажи что сейчас в vault

Перед удалением — посмотри что там есть:

```bash
find vault/ -name "*.md" | head -50
echo "---"
echo "Всего файлов:"
find vault/ -name "*.md" | wc -l
```

Убедись что это чужие данные (заметки о чужих делах, целях, клиентах) — и только потом продолжай.

---

## Шаг 4: Удали все личные данные

Удаляй строго по папкам — только содержимое, не сами папки:

```bash
# Ежедневные записи (голосовые, мысли, события)
rm -rf vault/daily/*

# Идеи, выводы, рефлексии
rm -rf vault/thoughts/ideas/*
rm -rf vault/thoughts/learnings/*
rm -rf vault/thoughts/reflections/*

# CRM — карточки клиентов и контакты
rm -rf vault/business/crm/*
rm -rf vault/business/network/*

# Проекты
rm -rf vault/projects/*

# Дайджесты и сводки
rm -rf vault/summaries/*

# Вложения (фото, файлы)
rm -rf vault/attachments/*

# Карты содержимого (MOC) — они авто-генерируются, можно стереть
rm -rf vault/MOC/*
```

---

## Шаг 5: Очисти память агента

Это самый важный файл — в нём накоплена долгосрочная память бота о прошлом владельце:

```bash
# Посмотри что внутри
cat vault/MEMORY.md
```

Если там чужие данные — перезапиши файл чистой заготовкой:

```bash
cat > vault/MEMORY.md << 'EOF'
# Agent Memory

## Core (always in context)
*Nothing yet. Will be populated as you use the bot.*

## Active
*Empty*

## Warm
*Empty*

## Cold
*Empty*

## Archive
*Empty*
EOF
```

---

## Шаг 6: Очисти цели и профиль пользователя

```bash
# Посмотри содержимое
cat vault/goals/0-vision-3y.md
cat vault/goals/1-yearly-2026.md
```

Если там чужие цели — замени на пустые заготовки:

```bash
cat > vault/goals/0-vision-3y.md << 'EOF'
# 3-Year Vision

*Not filled yet. Send a voice message to the bot describing your vision for the next 3 years.*
EOF

cat > vault/goals/1-yearly-2026.md << 'EOF'
# Goals 2026

*Not filled yet. Send a voice message to the bot describing your goals for this year.*
EOF

cat > vault/goals/2-monthly.md << 'EOF'
# Monthly Priorities

*Not filled yet.*
EOF

cat > vault/goals/3-weekly.md << 'EOF'
# Weekly Focus

*Not filled yet.*
EOF
```

---

## Шаг 7: Очисти профиль пользователя в скиллах

```bash
# Найди файл about.md
find vault/.claude -name "about.md" 2>/dev/null
```

Если нашёл — посмотри содержимое и замени на пустую заготовку:

```bash
ABOUT_FILE=$(find vault/.claude -name "about.md" 2>/dev/null | head -1)

if [ -n "$ABOUT_FILE" ]; then
    cat "$ABOUT_FILE"   # посмотри что там
    cat > "$ABOUT_FILE" << 'EOF'
# About the User

*Not filled yet. The bot will learn about you from your voice messages over time.*
EOF
    echo "Cleaned: $ABOUT_FILE"
fi
```

---

## Шаг 8: Проверь что ничего личного не осталось

```bash
# Ищем любые файлы с содержимым (не пустые и не заготовки)
echo "=== Файлы в vault (кроме .claude) ==="
find vault/ -name "*.md" -not -path "vault/.claude/*" | while read f; do
    lines=$(wc -l < "$f")
    echo "$lines строк: $f"
done

echo ""
echo "=== Содержимое MEMORY.md ==="
cat vault/MEMORY.md
```

Убедись что нигде нет чужих имён, проектов, клиентов.

---

## Шаг 9: Запусти бота заново

```bash
sudo systemctl start d-brain-bot
sleep 3
sudo systemctl status d-brain-bot
```

Должно быть `active (running)`.

---

## Шаг 10: Проверь в Telegram

1. Открой своего бота в Telegram
2. Отправь: `расскажи что ты знаешь обо мне`
3. Бот должен ответить что **ничего не знает** — vault пустой, начинаем с нуля
4. Отправь голосовое с коротким рассказом о себе — бот начнёт наполнять свою память твоими данными

---

## Что делать дальше

Бот теперь твой и пустой. Он будет узнавать тебя постепенно — через голосовые сообщения, которые ты ему отправляешь. Не нужно ничего заполнять вручную.

Просто начни разговаривать с ним как с ассистентом:
- Расскажи голосом о себе, своей работе, своих целях
- Диктуй мысли, задачи, идеи как будто говоришь вслух
- Каждый вечер в 21:00 будет приходить отчёт

Посмотреть логи если что-то не так:
```bash
sudo journalctl -u d-brain-bot -f
```
