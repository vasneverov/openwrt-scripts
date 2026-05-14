# Промпт для настройки free-claude-code + DeepSeek

Скопируй этот промпт и покажи Claude Code. Он сам всё настроит с нуля.

---

Привет. Нужно настроить free-claude-code для работы через DeepSeek (v4-flash/v4-pro).

## Что нужно сделать:

### 1. Клонировать и установить free-claude-code

```bash
cd /tmp
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code
uv tool install --force .
```

### 2. Создать .env

Создай файл `/Users/vas/CLAUDECODE/.env`:

```
# DeepSeek
DEEPSEEK_API_KEY=sk-fb954111068c40ab927ff19b941f5504

# Default model (DeepSeek flash)
MODEL=deepseek/deepseek-v4-flash
MODEL_SONNET=deepseek/deepseek-v4-flash
MODEL_OPUS=deepseek/deepseek-v4-pro
MODEL_HAIKU=deepseek/deepseek-v4-flash
```

### 3. Пропатчить подмену модели в SSE для DeepSeek

DeepSeek использует `AnthropicMessagesTransport`. Нужно подменить model в SSE на лету, чтобы Claude Code показывал `deepseek-v4-flash` вместо `deepseek/deepseek-v4-flash`.

Открой `/tmp/free-claude-code/providers/anthropic_messages.py`, найди метод `_transform_stream_event` и замени его содержимое на:

```python
    def _transform_stream_event(
        self,
        event: str,
        state: Any,
        *,
        thinking_enabled: bool,
    ) -> str | None:
        """Transform or drop a grouped SSE event before yielding it downstream."""
        if isinstance(state, NativeSseBlockPolicyState):
            event = transform_native_sse_block_event(
                event, state, thinking_enabled=thinking_enabled
            )
            if event is None:
                return None
        # Подмена model в message_start для DeepSeek
        if self._provider_name == "DEEPSEEK" and event and '"message_start"' in event:
            import re
            event = re.sub(
                r'"model"\s*:\s*"deepseek/deepseek-(v4-flash|v4-pro)"',
                r'"model":"deepseek-\1"',
                event,
            )
        return event
```

### 4. Пропатчить список моделей (оставить только DeepSeek flash и pro)

Открой `/tmp/free-claude-code/api/routes.py`, сделай 3 правки:

**Правка A** — замени `SUPPORTED_CLAUDE_MODELS` на пустой список:
```python
SUPPORTED_CLAUDE_MODELS: list[ModelResponse] = []
```

**Правка B** — в функции `_append_provider_model_variants` убери вариант "no thinking":
```python
def _append_provider_model_variants(
    models: list[ModelResponse],
    seen: set[str],
    provider_model_ref: str,
    *,
    supports_thinking: bool | None = None,
) -> None:
    _append_unique_model(
        models,
        seen,
        _discovered_model_response(
            gateway_model_id(provider_model_ref),
            display_name=provider_model_ref,
        ),
    )
```

**Правка C** — в функции `_build_models_list_response` убери блок `cached_prefixed_model_infos`:
```python
    # Не добавляем модели из cached_prefixed_model_infos
```

### 5. Переустановить пакет

```bash
cd /tmp/free-claude-code
uv tool install --reinstall .
```

### 6. Запустить сервер

```bash
cd /Users/vas/CLAUDECODE
FCC_ENV_FILE=/Users/vas/CLAUDECODE/.env nohup fcc-server > /tmp/fcc-server.log 2>&1 &

# Проверить
curl http://127.0.0.1:8082/health
```

### 7. Создать скрипты-обёртки

**`~/.local/bin/ds`** — DeepSeek v4-flash (с фоновым watcher для real-time обновления расхода):
```bash
#!/usr/bin/env bash
set -e
curl -sf http://127.0.0.1:8082/health >/dev/null || { echo "fcc-server не запущен"; exit 1; }
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN
export ANTHROPIC_API_KEY=freecc ANTHROPIC_BASE_URL=http://127.0.0.1:8082 ANTHROPIC_MODEL=deepseek-v4-flash

LOG_FILE=$(mktemp /tmp/claude-log-XXXXXX.jsonl)

# Фоновый watcher — парсит лог и обновляет cost трекер в реальном времени
(
  LAST_IN=0
  LAST_OUT=0
  while [ -f "$LOG_FILE" ]; do
    line=$(grep -o '"usage":{[^}]*}' "$LOG_FILE" 2>/dev/null | tail -1)
    if [ -n "$line" ]; then
      in_tok=$(echo "$line" | grep -o '"input_tokens":[0-9]*' | head -1 | sed 's/.*://')
      out_tok=$(echo "$line" | grep -o '"output_tokens":[0-9]*' | head -1 | sed 's/.*://')
      if [ -n "$in_tok" ] && [ -n "$out_tok" ] && [ "$in_tok" -gt "$LAST_IN" ] && [ "$out_tok" -gt "$LAST_OUT" ]; then
        delta_in=$((in_tok - LAST_IN))
        delta_out=$((out_tok - LAST_OUT))
        LAST_IN=$in_tok
        LAST_OUT=$out_tok
        echo "{\"usage\":{\"input_tokens\":$delta_in,\"output_tokens\":$delta_out},\"model\":{\"id\":\"deepseek-v4-flash\"}}" | bash "$HOME/.claude/hooks/ds-cost-tracker.sh" >/dev/null 2>&1
      fi
    fi
    sleep 2
  done
) &
WATCHER_PID=$!

claude --bare --settings /dev/null --log "$LOG_FILE" "$@"
EXIT_CODE=$?

kill $WATCHER_PID 2>/dev/null
rm -f "$LOG_FILE"

exit $EXIT_CODE
```

**`~/.local/bin/dsp`** — DeepSeek v4-pro (с фоновым watcher):
```bash
#!/usr/bin/env bash
set -e
curl -sf http://127.0.0.1:8082/health >/dev/null || { echo "fcc-server не запущен"; exit 1; }
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN
export ANTHROPIC_API_KEY=freecc ANTHROPIC_BASE_URL=http://127.0.0.1:8082 ANTHROPIC_MODEL=deepseek-v4-pro

LOG_FILE=$(mktemp /tmp/claude-log-XXXXXX.jsonl)

(
  LAST_IN=0
  LAST_OUT=0
  while [ -f "$LOG_FILE" ]; do
    line=$(grep -o '"usage":{[^}]*}' "$LOG_FILE" 2>/dev/null | tail -1)
    if [ -n "$line" ]; then
      in_tok=$(echo "$line" | grep -o '"input_tokens":[0-9]*' | head -1 | sed 's/.*://')
      out_tok=$(echo "$line" | grep -o '"output_tokens":[0-9]*' | head -1 | sed 's/.*://')
      if [ -n "$in_tok" ] && [ -n "$out_tok" ] && [ "$in_tok" -gt "$LAST_IN" ] && [ "$out_tok" -gt "$LAST_OUT" ]; then
        delta_in=$((in_tok - LAST_IN))
        delta_out=$((out_tok - LAST_OUT))
        LAST_IN=$in_tok
        LAST_OUT=$out_tok
        echo "{\"usage\":{\"input_tokens\":$delta_in,\"output_tokens\":$delta_out},\"model\":{\"id\":\"deepseek-v4-pro\"}}" | bash "$HOME/.claude/hooks/ds-cost-tracker.sh" >/dev/null 2>&1
      fi
    fi
    sleep 2
  done
) &
WATCHER_PID=$!

claude --bare --settings /dev/null --log "$LOG_FILE" "$@"
EXIT_CODE=$?

kill $WATCHER_PID 2>/dev/null
rm -f "$LOG_FILE"

exit $EXIT_CODE
```

Сделать исполняемыми:
```bash
chmod +x ~/.local/bin/ds ~/.local/bin/dsp
```

### 8. Настроить статус-бар (расход в $ + баланс DeepSeek в ¥)

Создай `~/.claude/hooks/ds-cost-tracker.sh`:
```bash
#!/usr/bin/env bash
# DeepSeek cost tracker — accumulates token usage and shows cost in dollars
COST_FILE="$HOME/.claude/.ds-cost.json"
if [ ! -f "$COST_FILE" ]; then
  echo '{"flash":{"in":0,"out":0},"pro":{"in":0,"out":0}}' > "$COST_FILE"
fi
input=$(cat)
in_tok=$(echo "$input" | jq -r '.usage.input_tokens // 0' 2>/dev/null)
out_tok=$(echo "$input" | jq -r '.usage.output_tokens // 0' 2>/dev/null)
model=$(echo "$input" | jq -r '.model.id // ""' 2>/dev/null)
if echo "$model" | grep -qi "deepseek-v4-flash\|deepseek.*flash"; then
  model_type="flash"
elif echo "$model" | grep -qi "deepseek-v4-pro\|deepseek.*pro"; then
  model_type="pro"
else
  echo '{"cost_dollars":0,"model":""}'
  exit 0
fi
current=$(cat "$COST_FILE")
new_in=$(( $(echo "$current" | jq -r ".${model_type}.in") + in_tok ))
new_out=$(( $(echo "$current" | jq -r ".${model_type}.out") + out_tok ))
echo "$current" | jq ".${model_type}.in = $new_in | .${model_type}.out = $new_out" > "$COST_FILE"
if [ "$model_type" = "flash" ]; then
  cost_dollars=$(echo "scale=6; ($new_in * 0.15 + $new_out * 0.60) / 1000000" | bc 2>/dev/null || echo "0")
else
  cost_dollars=$(echo "scale=6; ($new_in * 0.60 + $new_out * 2.40) / 1000000" | bc 2>/dev/null || echo "0")
fi
cost_rounded=$(printf "%.2f" "$cost_dollars" 2>/dev/null || echo "0")
echo "{\"cost_dollars\":$cost_rounded,\"model\":\"$model_type\"}"
```

Создай `~/.claude/statusline-command.sh`:
```bash
#!/bin/bash
# Claude Code Status Line — DeepSeek only: cost + balance
# Читает накопленный расход из файла, баланс из DeepSeek API (кэш 5 мин)

BLUE="\033[34m"; GREEN="\033[32m"; YELLOW="\033[33m"; RESET="\033[0m"

# DeepSeek cost (из накопленного файла)
COST_FILE="$HOME/.claude/.ds-cost.json"
ds_cost_status=""
if [ -f "$COST_FILE" ]; then
  flash_in=$(jq -r '.flash.in // 0' "$COST_FILE" 2>/dev/null)
  flash_out=$(jq -r '.flash.out // 0' "$COST_FILE" 2>/dev/null)
  pro_in=$(jq -r '.pro.in // 0' "$COST_FILE" 2>/dev/null)
  pro_out=$(jq -r '.pro.out // 0' "$COST_FILE" 2>/dev/null)

  flash_cost=$(echo "scale=6; ($flash_in * 0.15 + $flash_out * 0.60) / 1000000" | bc 2>/dev/null || echo "0")
  pro_cost=$(echo "scale=6; ($pro_in * 0.60 + $pro_out * 2.40) / 1000000" | bc 2>/dev/null || echo "0")
  total_cost=$(echo "scale=6; $flash_cost + $pro_cost" | bc 2>/dev/null || echo "0")
  cost_rounded=$(printf "%.2f" "$total_cost" 2>/dev/null || echo "0")

  if [ "$(echo "$total_cost > 0" | bc 2>/dev/null)" = "1" ]; then
    ds_cost_status="${BLUE}DS:\$${cost_rounded}${RESET}"
  fi
fi

# DeepSeek balance (cached 5 min)
BALANCE_CACHE="$HOME/.claude/.ds-balance.cache"
ds_balance=""
if [ -f "$BALANCE_CACHE" ]; then
  cache_age=$(($(date +%s) - $(stat -f %m "$BALANCE_CACHE" 2>/dev/null || echo 0)))
else
  cache_age=999
fi
if [ "$cache_age" -lt 300 ] && [ -s "$BALANCE_CACHE" ]; then
  ds_balance=$(cat "$BALANCE_CACHE")
else
  ds_key=$(grep DEEPSEEK_API_KEY /Users/vas/CLAUDECODE/.env 2>/dev/null | head -1 | sed 's/.*=//;s/"//g')
  if [ -n "$ds_key" ]; then
    balance_json=$(curl -s --max-time 5 https://api.deepseek.com/user/balance \
      -H "Authorization: Bearer $ds_key" 2>/dev/null)
    if [ -n "$balance_json" ]; then
      cny=$(echo "$balance_json" | jq -r '.balance_infos[] | select(.currency=="CNY") | .total_balance' 2>/dev/null)
      if [ -n "$cny" ] && [ "$cny" != "null" ] && [ "$cny" != "" ]; then
        ds_balance="¥${cny}"
        echo "$ds_balance" > "$BALANCE_CACHE"
      else
        usd=$(echo "$balance_json" | jq -r '.balance_infos[] | select(.currency=="USD") | .total_balance' 2>/dev/null)
        if [ -n "$usd" ] && [ "$usd" != "null" ] && [ "$usd" != "" ]; then
          ds_balance="\$${usd}"
          echo "$ds_balance" > "$BALANCE_CACHE"
        fi
      fi
    fi
  fi
fi

# Build status line
parts=()
if [ -n "$ds_cost_status" ]; then parts+=("$ds_cost_status"); fi
if [ -n "$ds_balance" ]; then parts+=("${GREEN}${ds_balance}${RESET}"); fi
result=""
for part in "${parts[@]}"; do
  if [ -n "$result" ]; then result="$result │ $part"; else result="$part"; fi
done
printf "%b" "$result"
```

Сделать исполняемыми:
```bash
chmod +x ~/.claude/hooks/ds-cost-tracker.sh ~/.claude/statusline-command.sh
```

### 9. Проверка

```bash
# DeepSeek flash
ds -p "привет, какая модель?"
# → deepseek-v4-flash

# DeepSeek pro
dsp -p "привет, какая модель?"
# → deepseek-v4-pro

# Статус-бар показывает:
# DS:$0.00 │ ¥29.57
```
