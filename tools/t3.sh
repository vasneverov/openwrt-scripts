#!/bin/bash
# t3.sh — Ремонт 3 роутеров в параллельных tmux-панелях
# Использование: bash ~/CLAUDECODE/tools/t3.sh <ip1> <ip2> <ip3>
# Запускается из основного Claude (или вручную)
# Должен быть запущен ВНУТРИ tmux-сессии

set -e

R1="${1:?Нужен IP роутера 1}"
R2="${2:?Нужен IP роутера 2}"
R3="${3:?Нужен IP роутера 3}"

WINDOW_NAME="r:${R1##*.}|${R2##*.}|${R3##*.}"
PROMPT_SCRIPT="$HOME/CLAUDECODE/tools/gen-repair-prompt.sh"
CLAUDE_BIN="$HOME/.local/bin/claude"

if [ -z "$TMUX" ]; then
  echo "ОШИБКА: Нужно запустить внутри tmux. Сначала запусти: tbox"
  exit 1
fi

echo "🔧 Создаю окно агентов: $WINDOW_NAME"

# Создаём новое окно для агентов
tmux new-window -n "$WINDOW_NAME"
AGENTS_WIN="$WINDOW_NAME"

# Делим окно на 3 горизонтальные колонки
tmux split-window -t "$AGENTS_WIN" -h
tmux split-window -t "$AGENTS_WIN".2 -h
tmux select-layout -t "$AGENTS_WIN" even-horizontal

# Подписываем панели
tmux select-pane -t "$AGENTS_WIN".1 -T "🔧 $R1"
tmux select-pane -t "$AGENTS_WIN".2 -T "🔧 $R2"
tmux select-pane -t "$AGENTS_WIN".3 -T "🔧 $R3"

# Включаем показ заголовков панелей
tmux set-option -t "$AGENTS_WIN" pane-border-status top

# Генерируем промты и запускаем агентов
PROMPT1=$(bash "$PROMPT_SCRIPT" "$R1")
PROMPT2=$(bash "$PROMPT_SCRIPT" "$R2")
PROMPT3=$(bash "$PROMPT_SCRIPT" "$R3")

# Запускаем claude в каждой панели
# Используем heredoc через файлы чтобы избежать экранирования
TMPDIR=$(mktemp -d)
echo "$PROMPT1" > "$TMPDIR/p1.txt"
echo "$PROMPT2" > "$TMPDIR/p2.txt"
echo "$PROMPT3" > "$TMPDIR/p3.txt"

tmux send-keys -t "$AGENTS_WIN".1 \
  "$CLAUDE_BIN --dangerously-skip-permissions --output-format text -p \"\$(cat $TMPDIR/p1.txt)\" --add-dir \$HOME/CLAUDECODE 2>&1 | tee /tmp/agent-$R1.log" \
  Enter

tmux send-keys -t "$AGENTS_WIN".2 \
  "$CLAUDE_BIN --dangerously-skip-permissions --output-format text -p \"\$(cat $TMPDIR/p2.txt)\" --add-dir \$HOME/CLAUDECODE 2>&1 | tee /tmp/agent-$R2.log" \
  Enter

tmux send-keys -t "$AGENTS_WIN".3 \
  "$CLAUDE_BIN --dangerously-skip-permissions --output-format text -p \"\$(cat $TMPDIR/p3.txt)\" --add-dir \$HOME/CLAUDECODE 2>&1 | tee /tmp/agent-$R3.log" \
  Enter

echo "✅ Агенты запущены в окне: $WINDOW_NAME"
echo "   Ctrl+B → w  — список окон"
echo "   Ctrl+B → 2  — переключиться на агентов"
echo "   Логи: /tmp/agent-<IP>.log"

# Переключаемся на окно агентов
tmux select-window -t "$AGENTS_WIN"
