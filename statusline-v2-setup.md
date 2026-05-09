# Status Line v2 — Setup Guide

Упрощённая статусная строка с токенами, временем сессии и кастомными API.

## Что показывается

```
Claude Son 4.6 │ ctx:████░░░░ 45% │ ⏰2ч 15м │ tk:45k/155k │ Al:██░░░░░░ 35% │ Km:███░░░░░ 42%
```

| Блок | Описание |
|------|----------|
| `Claude Son 4.6` | Сокращённое название модели |
| `ctx:████░░░░ 45%` | Заполненность контекста (основной индикатор) |
| `⏰2ч 15м` | Оставшееся время до сброса 5-часового лимита |
| `tk:45k/155k` | Токенов использовано / осталось |
| `Al:██░░░░░░ 35%` | Alamo weekly usage (кастомный) |
| `Km:███░░░░░ 42%` | KIMI weekly usage (кастомный) |

**Цвета:** 🟢 < 60% 🟡 60-79% 🔴 ≥ 80%

---

## Установка

### Шаг 1: Замени скрипт

```bash
# Создай бэкап старого
cp ~/.claude/statusline-command.sh ~/.claude/statusline-command.sh.backup

# Скопируй новый
cp ~/.claude/statusline-command-v2.sh ~/.claude/statusline-command.sh
chmod +x ~/.claude/statusline-command.sh
```

### Шаг 2: Настрой settings.json

В `~/.claude/settings.json` должно быть:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline-command.sh"
  }
}
```

### Шаг 3: Перезапусти Claude Code

---

## Настройка кастомных API (Alamo, KIMI)

### Ручное обновление

```bash
# Установи процент использования Alamo
~/.claude/.api-status/update-alamo.sh 45

# Установи процент использования KIMI
cat > ~/.claude/.api-status/kimi-weekly.json << 'EOF'
{
  "used_pct": 42,
  "provider": "kimi",
  "updated": "2026-04-25T10:30:00Z"
}
EOF
```

### Авто-обновление через cron

```bash
# Открой crontab
crontab -e

# Добавь (обновление каждые 15 минут)
*/15 * * * * ~/.claude/.api-status/update-all.sh
```

### Интеграция с реальными API

Создай скрипт который будет:
1. Делать API запрос к Alamo/KIMI
2. Парсить usage/limit
3. Считать percentage
4. Писать в JSON

Пример заглушки для Alamo API:

```bash
#!/bin/bash
# ~/.claude/.api-status/update-alamo-real.sh

API_KEY="$ALAMO_API_KEY"
RESPONSE=$(curl -s -H "Authorization: Bearer $API_KEY" \
  "https://api.alamo.ai/v1/usage/weekly")

USED=$(echo "$RESPONSE" | jq '.tokens_used')
LIMIT=$(echo "$RESPONSE" | jq '.tokens_limit')
PCT=$(echo "scale=1; $USED * 100 / $LIMIT" | bc)

cat > ~/.claude/.api-status/alamo-weekly.json << EOF
{
  "used_pct": $PCT,
  "provider": "alamo",
  "updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
```

---

## Что убрано (по сравнению с v1)

- ❌ Email и статус логина (лишний текст)
- ❌ Текущая директория (cwd) — видно в prompt
- ❌ 7-дневный Claude Code лимит (редко достигается)
- ❌ Доллары / extra / баланс (неактуально)

---

## Формат токенов

| Значение | Формат |
|----------|--------|
| 1500 | 1500 |
| 45000 | 45k |
| 1500000 | 1M |

---

## Результат

Чистая строка с **только нужной** информацией:
- Модель
- Контекст (главный индикатор)
- Время до сброса сессии
- Токены
- Кастомные API (если настроены)
