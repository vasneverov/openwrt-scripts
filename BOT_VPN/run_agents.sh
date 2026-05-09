#!/bin/bash
# ============================================================
# XUI-BOT — Запуск Claude Code в tmux с bypass подтверждений
#
# Использование:
#   chmod +x run_agents.sh
#   ./run_agents.sh
# ============================================================

SESSION="xui-bot"
PROJECT_DIR="$HOME/xui-bot"
PROMPT_FILE="$(dirname "$0")/PROMPT_FOR_CLAUDECODE.md"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== XUI-BOT Agent Launcher ===${NC}"
echo ""

# Проверить наличие tmux
if ! command -v tmux &> /dev/null; then
    echo "Устанавливаю tmux..."
    sudo apt-get install -y tmux 2>/dev/null || brew install tmux 2>/dev/null
fi

# Проверить наличие claude
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}⚠️  Claude Code не найден.${NC}"
    echo "Установи: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

# Создать папку проекта
mkdir -p "$PROJECT_DIR"

# Убить старую сессию если есть
tmux kill-session -t "$SESSION" 2>/dev/null

echo -e "${GREEN}Запускаю tmux сессию '$SESSION'...${NC}"

# Создать новую tmux сессию (3 панели)
# ┌─────────────────┬────────────────┐
# │                 │  Лог файлов    │
# │  Claude Code    ├────────────────┤
# │                 │  Статус        │
# └─────────────────┴────────────────┘

tmux new-session -d -s "$SESSION" -x 220 -y 55

# Правая колонка — разбить на две панели
tmux split-window -h -t "$SESSION:0" -p 35
tmux split-window -v -t "$SESSION:0.1" -p 50

# Левая панель (0.0) — Claude Code
# Правая верхняя (0.1) — лог файлов
# Правая нижняя (0.2) — статус агентов

# Настроить правую верхнюю — лог файлов
tmux send-keys -t "$SESSION:0.1" \
    "echo '📁 Файлы проекта:' && watch -n 3 'find $PROJECT_DIR -name \"*.py\" -o -name \"*.yml\" -o -name \"*.txt\" | sort | head -25'" \
    Enter

# Настроить правую нижнюю — статус
tmux send-keys -t "$SESSION:0.2" \
    "echo '📊 Статус агентов:' && watch -n 5 'echo \"Файлов создано: \$(find $PROJECT_DIR -type f | wc -l)\" && echo \"Строк кода: \$(find $PROJECT_DIR -name \"*.py\" | xargs wc -l 2>/dev/null | tail -1)\"'" \
    Enter

# Переключиться на основную панель и запустить Claude Code
tmux select-pane -t "$SESSION:0.0"

echo -e "${GREEN}✅ tmux сессия создана${NC}"
echo ""
echo -e "${YELLOW}Запускаю Claude Code с bypass подтверждений...${NC}"
echo ""

# Запустить Claude Code с:
# --dangerously-skip-permissions — без подтверждений
# Передать промпт из файла
tmux send-keys -t "$SESSION:0.0" \
    "cd $PROJECT_DIR && claude --dangerously-skip-permissions < '$PROMPT_FILE'" \
    Enter

# Подключиться к сессии
echo "Подключаюсь к tmux сессии..."
echo "(Для выхода без закрытия: Ctrl+B, затем D)"
echo ""

tmux attach-session -t "$SESSION"
