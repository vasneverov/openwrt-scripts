#!/bin/bash
# =============================================================================
# Запуск DeepSeek в iTerm2 — интерфейс как у Claude Code CLI
# =============================================================================
# Просто запусти этот скрипт в iTerm2:
#   ./run-deepseek-iterm2.sh
#
# Доступные модели DeepSeek:
#   deepseek-v4-flash  — быстрая, дешёвая ($0.07/$0.27 за 1M токенов)
#   deepseek-v4-pro    — умная, дороже ($0.70/$2.70 за 1M токенов)
#
# Для прошивок роутеров достаточно Flash.
# =============================================================================

cd /Users/vas/CLAUDECODE

# Ключ DeepSeek (OpenAI-совместимый API)
export DEEPSEEK_API_KEY="sk-7253edfd69f8438ca39b911ae597ad8e"
export OPENAI_API_KEY="$DEEPSEEK_API_KEY"
export OPENAI_API_BASE="https://api.deepseek.com/v1"

# Добавляем Python bin в PATH (там лежит aider)
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# Установка aider если не установлен
if ! command -v aider &> /dev/null; then
  echo "Устанавливаю aider-chat..."
  pip3 install aider-chat
fi

# Выбор модели (с префиксом openai/ для litellm)
MODEL="${1:-openai/deepseek-v4-flash}"

# Запуск DeepSeek
echo "═══════════════════════════════════════════"
echo "  Модель: $MODEL"
echo "  API: api.deepseek.com/v1"
echo "  Рабочая папка: /Users/vas/CLAUDECODE"
echo "  Без auto-prove — команды не прерываются"
echo "═══════════════════════════════════════════"
echo ""

aider --model "$MODEL" --no-show-model-warnings --dark-mode
