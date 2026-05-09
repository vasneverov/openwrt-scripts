#!/bin/bash
# Обновление статуса агента в tmux панели
# Использование: ./tmux-status-updater.sh [pane_number] [status] [ip] [task]

PANE=${1:-0}
STATUS=${2:-"ОЖИДАНИЕ"}
IP=${3:-"[не назначен]"}
TASK=${4:-"[ожидание]"}

# Цвета
GREEN="#[fg=green]"
RED="#[fg=red]"
YELLOW="#[fg=yellow]"
RESET="#[default]"

# Определяем цвет статуса
if [[ "$STATUS" == *"✓"* ]] || [[ "$STATUS" == *"DONE"* ]] || [[ "$STATUS" == *"ГОТОВО"* ]]; then
    STATUS_COLOR="${GREEN}"
elif [[ "$STATUS" == *"❌"* ]] || [[ "$STATUS" == *"ERROR"* ]] || [[ "$STATUS" == *"ОШИБКА"* ]]; then
    STATUS_COLOR="${RED}"
else
    STATUS_COLOR="${YELLOW}"
fi

# Формируем вывод
OUTPUT="
╔════════════════════════════════════════════════╗
║  ПАНЕЛЬ $PANE                                   ║
╠════════════════════════════════════════════════╣
║  Статус: ${STATUS_COLOR}${STATUS}${RESET}
║  IP: ${IP}
║  Задача: ${TASK}
║  Время: $(date '+%H:%M:%S')
╚════════════════════════════════════════════════╝
"

echo -e "$OUTPUT"
