# Установка статусной строки Claude Code

Выполни эти шаги в своём Claude Code (можно просто вставить как промт).

---

## Шаг 1 — Создай скрипт

Создай файл `~/.claude/statusline-command.sh`:

```bash
#!/bin/bash
# Claude Code Status Line

input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

home="$HOME"
short_cwd="${cwd/#$home/~}"

auth_cache="/tmp/claude_auth_status_cache"
if [ -f "$auth_cache" ] && [ $(( $(date +%s) - $(stat -f %m "$auth_cache" 2>/dev/null || echo 0) )) -lt 60 ]; then
  IFS='|' read -r auth_ok auth_email < "$auth_cache"
else
  auth_json=$(claude auth status 2>/dev/null)
  logged_in=$(echo "$auth_json" | jq -r '.loggedIn // false')
  auth_email=$(echo "$auth_json" | jq -r '.email // ""')
  if [ "$logged_in" = "true" ]; then
    auth_ok="true"
  else
    auth_ok="false"
  fi
  echo "${auth_ok}|${auth_email}" > "$auth_cache"
fi

GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

build_bar() {
  local pct=$1
  local width=6
  local filled=$(( pct * width / 100 ))
  local bar="" i
  for i in $(seq 1 $width); do
    if [ "$i" -le "$filled" ]; then bar="${bar}█"; else bar="${bar}░"; fi
  done
  echo "$bar"
}

pct_color() {
  local pct=$1
  if   [ "$pct" -ge 80 ]; then echo "$RED"
  elif [ "$pct" -ge 60 ]; then echo "$YELLOW"
  else                          echo "$GREEN"
  fi
}

if [ "$auth_ok" = "true" ]; then
  user_part="${GREEN}✅ логин ОК на ${auth_email}${RESET}"
else
  user_part="логин НЕТ"
fi

parts=()
parts+=("$user_part")
parts+=("$model")
if [ -n "$short_cwd" ]; then
  parts+=("$short_cwd")
fi

if [ -n "$used_pct" ]; then
  used_int=$(printf "%.0f" "$used_pct")
  bar=$(build_bar "$used_int")
  color=$(pct_color "$used_int")
  parts+=("ctx:${color}${bar} ${used_int}%${RESET}")
fi

five=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
week=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
if [ -n "$five" ]; then
  five_int=$(printf '%.0f' "$five")
  bar=$(build_bar "$five_int")
  color=$(pct_color "$five_int")
  parts+=("5h:${color}${bar} ${five_int}%${RESET}")
fi
if [ -n "$week" ]; then
  week_int=$(printf '%.0f' "$week")
  bar=$(build_bar "$week_int")
  color=$(pct_color "$week_int")
  parts+=("7d:${color}${bar} ${week_int}%${RESET}")
fi

vim_mode=$(echo "$input" | jq -r '.vim.mode // empty')
if [ -n "$vim_mode" ]; then
  parts+=("[$vim_mode]")
fi

result=""
for part in "${parts[@]}"; do
  if [ -n "$result" ]; then
    result="$result | $part"
  else
    result="$part"
  fi
done

printf "%b" "$result"
```

## Шаг 2 — Права на исполнение

```bash
chmod +x ~/.claude/statusline-command.sh
```

## Шаг 3 — Настройки Claude Code

В файл `~/.claude/settings.json` добавь секцию `statusLine` (внутрь корневых фигурных скобок):

```json
"statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline-command.sh"
}
```

## Шаг 4 — Проверь jq

```bash
jq --version
```

Если нет — установи: `brew install jq`

## Шаг 5 — Перезапусти Claude Code

---

**Результат:**

```
✅ логин ОК на твой@email.com | Claude Sonnet 4.6 | ~/папка | ctx:█░░░░░ 8% | 5h:██░░░░ 34% | 7d:█░░░░░ 12%
```

Цвета: зелёный < 60%, жёлтый 60–79%, красный ≥ 80%.
Email подтягивается автоматически из твоей авторизации.
