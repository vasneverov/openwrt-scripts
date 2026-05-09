# Настройка Claude Code — полная инструкция

Этот файл настраивает Claude Code так же, как у Василия:
- Красивая статусная строка с прогресс-барами лимитов
- Автоматический bypass разрешений (не спрашивает подтверждений)
- Проверка авторизации при каждом запуске
- VS Code всегда открывается в рабочей папке
- Mac не засыпает во время работы

---

## Шаг 1 — Создай рабочую папку

```bash
mkdir -p ~/CLAUDECODE
```

---

## Шаг 2 — Скрипт статусной строки

Создай файл `~/.claude/statusline-command.sh`:

```bash
mkdir -p ~/.claude
```

Содержимое файла `~/.claude/statusline-command.sh`:

```bash
input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

five=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
week=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

home="$HOME"
short_cwd="${cwd/#$home/~}"

auth_cache="/tmp/claude_auth_status_cache"
if [ -f "$auth_cache" ] && [ $(( $(date +%s) - $(stat -f %m "$auth_cache" 2>/dev/null || stat -c %Y "$auth_cache" 2>/dev/null || echo 0) )) -lt 60 ]; then
  IFS='|' read -r auth_ok auth_email < "$auth_cache"
else
  auth_json=$(claude auth status 2>/dev/null)
  logged_in=$(echo "$auth_json" | jq -r '.loggedIn // false')
  auth_email=$(echo "$auth_json" | jq -r '.email // ""')
  if [ "$logged_in" = "true" ]; then auth_ok="true"; else auth_ok="false"; fi
  echo "${auth_ok}|${auth_email}" > "$auth_cache"
fi

GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

build_bar() {
  local pct=$1 width=6 filled bar="" i
  filled=$(( pct * width / 100 ))
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

if [ -n "$five" ]; then
  user_part="${GREEN}✅ логин ОК на ${auth_email}${RESET}"
elif [ "$auth_ok" = "true" ]; then
  user_part="${YELLOW}⏳ токен есть, сессии нет${RESET}"
else
  user_part="${RED}❌ логин НЕТ${RESET}"
fi

parts=("$user_part" "$model")
[ -n "$short_cwd" ] && parts+=("$short_cwd")

if [ -n "$used_pct" ]; then
  used_int=$(printf "%.0f" "$used_pct")
  bar=$(build_bar "$used_int"); color=$(pct_color "$used_int")
  parts+=("ctx:${color}${bar} ${used_int}%${RESET}")
fi

if [ -n "$five" ]; then
  five_int=$(printf '%.0f' "$five")
  bar=$(build_bar "$five_int"); color=$(pct_color "$five_int")
  five_resets_at=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
  reset_str=""
  if [ -n "$five_resets_at" ]; then
    now=$(date +%s)
    diff=$(( five_resets_at - now ))
    if [ "$diff" -gt 0 ]; then
      reset_h=$(( diff / 3600 )); reset_m=$(( (diff % 3600) / 60 ))
      reset_str=" ⏰ ${reset_h}ч ${reset_m}м"
    fi
  fi
  parts+=("5h:${color}${bar} ${five_int}%${RESET}${reset_str}")
fi

if [ -n "$week" ]; then
  week_int=$(printf '%.0f' "$week")
  bar=$(build_bar "$week_int"); color=$(pct_color "$week_int")
  parts+=("7d:${color}${bar} ${week_int}%${RESET}")
fi

result=""
for part in "${parts[@]}"; do
  [ -n "$result" ] && result="$result | $part" || result="$part"
done
printf "%b" "$result"
```

Сделай файл исполняемым:

```bash
chmod +x ~/.claude/statusline-command.sh
```

---

## Шаг 3 — Хук caffeinate (только macOS)

Создай файл `~/.claude/hooks/caffeinate-start.sh`:

```bash
mkdir -p ~/.claude/hooks
```

Содержимое:

```bash
if ! pgrep -x caffeinate > /dev/null; then
    caffeinate -d &
fi
exit 0
```

```bash
chmod +x ~/.claude/hooks/caffeinate-start.sh
```

> На Windows/Linux этот хук не нужен — просто не создавай этот файл и убери его из settings.json ниже.

---

## Шаг 4 — Настройки Claude Code

Создай/замени файл `~/.claude/settings.json`:

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/caffeinate-start.sh"
          }
        ]
      }
    ]
  },
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline-command.sh"
  },
  "language": "ru",
  "skipDangerousModePermissionPrompt": true,
  "defaultPermissionMode": "bypassPermissions"
}
```

> Если не Mac — удали блок `hooks` из settings.json полностью.

---

## Шаг 5 — Зависимости

Нужен `jq` для работы статусной строки:

**macOS:**
```bash
brew install jq
```

**Ubuntu/Debian:**
```bash
sudo apt install jq
```

**Windows (через WSL):**
```bash
sudo apt install jq
```

---

## Шаг 6 — VS Code + автозапуск

Добавь в конец файла `~/.zshrc` (или `~/.bashrc` на Linux):

```bash
# Claude Code — открывать VS Code в рабочей папке
alias code='command code ~/CLAUDECODE'

# Автозапуск claude в терминале VS Code + сброс кэша авторизации
if [[ "$TERM_PROGRAM" == "vscode" ]]; then
  rm -f /tmp/claude_auth_status_cache
  claude
fi
```

Применить изменения:
```bash
source ~/.zshrc
```

---

## Шаг 7 — Авторизация

```bash
claude auth login
```

Откроется браузер — войди в аккаунт Anthropic.

---

## Готово

После этих шагов:

| Что | Как выглядит |
|-----|-------------|
| Статусная строка | `✅ логин ОК на email | Claude Sonnet 4.6 | ~/CLAUDECODE | ctx:█░░░░░ 12% | 5h:████░░ 67% ⏰ 3ч 22м | 7d:█░░░░░ 18%` |
| Разрешения | Claude не спрашивает подтверждений |
| VS Code | `code` → открывается в `~/CLAUDECODE` и сразу запускает claude |
| Авторизация | Проверяется при каждом открытии терминала VS Code |

---

## Что означают индикаторы

### Статус авторизации (левая часть строки)

| Что видишь | Что это значит |
|---|---|
| `✅ логин ОК на email \| 🔑 ключ ✓` | Всё отлично: ключ в Keychain есть, авторизация активна, сессия запущена |
| `⏳ 🔑 ключ ✓ \| авторизация ✓ \| сессии нет` | Ключ есть, авторизован — просто сессия ещё не началась (нет активного чата) |
| `⚠️ 🔑 ключ ✓ \| авторизация ✗` | Ключ в Keychain найден, но авторизация слетела → выполни `claude auth login` |
| `❌ ключ не найден` | Ни ключа, ни авторизации → выполни `claude auth login` |

> **Где хранится ключ:**
> - macOS — в Keychain под именем `Claude Code-credentials` (не файл, а системное хранилище)
> - Linux — файл `~/.claude/.credentials.json`

### Лимиты (правая часть строки)

- **ctx** — заполнение контекстного окна текущего разговора
- **5h** — лимит запросов за 5 часов (сколько использовано), ⏰ — когда сбросится
- **7d** — недельный лимит запросов

Цвета: 🟢 зелёный < 60% · 🟡 жёлтый 60–79% · 🔴 красный ≥ 80%
