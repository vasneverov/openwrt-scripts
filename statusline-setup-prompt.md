# Задача: настрой мне красивую статусную строку в Claude Code

Помоги мне настроить кастомную статусную строку (statusline) для Claude Code CLI.

## Что должно получиться

Строка в нижней части терминала выглядит так:

```
✅ логин ОК на user@gmail.com | 🔑 ключ ✓ | Claude Sonnet 4.6 | ~/myproject | ctx:█░░░░░ 12% | 5h:████░░ 67% ⏰ 3ч 22м | 7d:█░░░░░ 18% обн. пн 21 апр
```

Что показывается:
- **Авторизация** — статус логина + email + наличие ключа
- **Модель** — текущая модель Claude
- **Директория** — текущая папка (сокращённая до `~`)
- **ctx:** — заполненность контекстного окна (прогресс-бар + %)
- **5h:** — использование 5-часового лимита + ⏰ сколько времени до сброса
- **7d:** — использование недельного лимита + дата обновления

Прогресс-бары: 6 символов `█`/`░`, цвет: зелёный < 60%, жёлтый 60–79%, красный ≥ 80%.

---

## Как это работает

Claude Code при каждом обновлении запускает указанный скрипт и передаёт ему JSON через **stdin**.
Скрипт читает его через `input=$(cat)`, парсит через `jq` и выводит строку с ANSI-цветами через `printf "%b"`.

Зависимости: `jq`, `claude` (в PATH), `bash`.

---

## Шаг 1. Создай скрипт `~/.claude/statusline-command.sh`

```bash
input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')

five=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
week=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

home="$HOME"
short_cwd="${cwd/#$home/~}"

has_key="false"
if command -v security &>/dev/null; then
  key_val=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null)
  [ -n "$key_val" ] && has_key="true"
elif [ -f "$HOME/.claude/.credentials.json" ]; then
  has_key="true"
fi

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
  user_part="${GREEN}✅ логин ОК на ${auth_email} | 🔑 ключ ✓${RESET}"
elif [ "$auth_ok" = "true" ] && [ "$has_key" = "true" ]; then
  user_part="${YELLOW}⏳ 🔑 ключ ✓ | авторизация ✓ | сессии нет${RESET}"
elif [ "$has_key" = "true" ]; then
  user_part="${YELLOW}⚠️ 🔑 ключ ✓ | авторизация ✗ — нужен claude auth login${RESET}"
else
  user_part="${RED}❌ ключ не найден — нужен claude auth login${RESET}"
fi

parts=()
parts+=("$user_part")
parts+=("$model")
[ -n "$short_cwd" ] && parts+=("$short_cwd")

if [ -n "$used_pct" ]; then
  used_int=$(printf "%.0f" "$used_pct")
  bar=$(build_bar "$used_int")
  color=$(pct_color "$used_int")
  parts+=("ctx:${color}${bar} ${used_int}%${RESET}")
fi

if [ -n "$five" ]; then
  five_int=$(printf '%.0f' "$five")
  bar=$(build_bar "$five_int")
  color=$(pct_color "$five_int")
  five_resets_at=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
  reset_str=""
  if [ -n "$five_resets_at" ]; then
    now=$(date +%s)
    diff=$(( five_resets_at - now ))
    if [ "$diff" -gt 0 ]; then
      reset_h=$(( diff / 3600 ))
      reset_m=$(( (diff % 3600) / 60 ))
      reset_str=" ⏰ ${reset_h}ч ${reset_m}м"
    fi
  fi
  parts+=("5h:${color}${bar} ${five_int}%${RESET}${reset_str}")
fi

if [ -n "$week" ]; then
  week_int=$(printf '%.0f' "$week")
  bar=$(build_bar "$week_int")
  color=$(pct_color "$week_int")
  week_resets_at=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')
  week_reset_str=""
  if [ -n "$week_resets_at" ]; then
    dow=$(date -r "$week_resets_at" +%u 2>/dev/null || date -d "@$week_resets_at" +%u 2>/dev/null)
    day=$(date -r "$week_resets_at" +%d 2>/dev/null || date -d "@$week_resets_at" +%d 2>/dev/null)
    mon=$(date -r "$week_resets_at" +%m 2>/dev/null || date -d "@$week_resets_at" +%m 2>/dev/null)
    case "$dow" in
      1) dow_ru="пн" ;; 2) dow_ru="вт" ;; 3) dow_ru="ср" ;;
      4) dow_ru="чт" ;; 5) dow_ru="пт" ;; 6) dow_ru="сб" ;; 7) dow_ru="вс" ;;
      *) dow_ru="" ;;
    esac
    case "$mon" in
      01) mon_ru="янв" ;; 02) mon_ru="фев" ;; 03) mon_ru="мар" ;;
      04) mon_ru="апр" ;; 05) mon_ru="май" ;; 06) mon_ru="июн" ;;
      07) mon_ru="июл" ;; 08) mon_ru="авг" ;; 09) mon_ru="сен" ;;
      10) mon_ru="окт" ;; 11) mon_ru="ноя" ;; 12) mon_ru="дек" ;;
      *) mon_ru="" ;;
    esac
    week_reset_str=" обн. ${dow_ru} ${day#0} ${mon_ru}"
  fi
  parts+=("7d:${color}${bar} ${week_int}%${RESET}${week_reset_str}")
fi

vim_mode=$(echo "$input" | jq -r '.vim.mode // empty')
if [ -n "$vim_mode" ]; then
  parts+=("[$vim_mode]")
fi

result=""
for part in "${parts[@]}"; do
  if [ -n "$result" ]; then result="$result | $part"; else result="$part"; fi
done

printf "%b" "$result"
```

## Шаг 2. Сделай скрипт исполняемым

```bash
chmod +x ~/.claude/statusline-command.sh
```

## Шаг 3. Подключи в настройках Claude Code

Добавь в `~/.claude/settings.json` (если файла нет — создай):

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline-command.sh"
  }
}
```

Или используй скилл `/statusline-setup`, если он доступен — он сам пропишет нужную строку в settings.json.

## Шаг 4. Проверь зависимости

```bash
which jq      # нужен jq
which claude  # нужен claude в PATH
```

Установить jq, если нет:
- macOS: `brew install jq`
- Ubuntu/Debian: `sudo apt install jq`

## Шаг 5. Перезапусти Claude Code

Закрой и снова открой — статусная строка появится внизу.

---

## Примечания

- Блоки `5h:` и `7d:` появляются только после первого запроса к API в сессии (когда Claude Code начнёт передавать данные о лимитах).
- `stat -f %m` — macOS-синтаксис, `stat -c %Y` — Linux. Скрипт поддерживает оба.
- Авторизация кешируется в `/tmp/claude_auth_status_cache` на 60 секунд — чтобы не тормозить.
- Ключ ищется в macOS Keychain (`security find-generic-password`), затем в `~/.claude/.credentials.json`.
- На Linux блок `has_key` через Keychain не сработает — скрипт автоматически упадёт на проверку файла.
