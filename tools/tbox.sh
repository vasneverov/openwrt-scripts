#!/bin/bash
# tbox.sh — запуск tmux-сессии "tbox" с Claude Code
# Использование: bash ~/CLAUDECODE/tools/tbox.sh
# Или через алиас: tbox

SESSION="tbox"

if [ -n "$TMUX" ]; then
  # Уже в tmux — просто запускаем claude
  exec claude "$@"
fi

# Создаём сессию если нет
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -n "chat" -x "$(tput cols)" -y "$(tput lines)"
  # Запускаем claude в окне chat
  tmux send-keys -t "$SESSION:chat" "claude" Enter
  tmux attach-session -t "$SESSION"
else
  # Сессия есть — просто присоединяемся
  tmux attach-session -t "$SESSION"
fi
