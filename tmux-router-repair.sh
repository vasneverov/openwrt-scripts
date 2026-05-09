#!/bin/bash
# Tmux session для параллельного ремонта 3 роутеров
# Запуск: ./tmux-router-repair.sh

SESSION_NAME="router-repair-$(date +%H%M)"

# Удаляем старую сессию если есть
tmux kill-session -t $SESSION_NAME 2>/dev/null

# Создаём новую сессию
tmux new-session -d -s $SESSION_NAME -n "repair"

# Делим окно на 3 панели
# Сначала делим вертикально (левая | правая)
tmux split-window -h -t $SESSION_NAME

# Правую часть делим горизонтально (верхняя | нижняя)
tmux split-window -v -t $SESSION_NAME:0.1

# Настраиваем layout (3 панели: слева большая, справа 2 маленькие)
tmux select-layout -t $SESSION_NAME main-vertical

# Отправляем команды в каждую панель
# Панель 0: Координатор (я)
tmux send-keys -t $SESSION_NAME:0.0 'echo "╔═══════════════════════════════════════╗"' C-m
tmux send-keys -t $SESSION_NAME:0.0 'echo "║  ПАНЕЛЬ 1: КООРДИНАТОР (Claude)      ║"' C-m
tmux send-keys -t $SESSION_NAME:0.0 'echo "╚═══════════════════════════════════════╝"' C-m
tmux send-keys -t $SESSION_NAME:0.0 'echo "Ожидание задачи..."' C-m

# Панель 1: Агент 1
tmux send-keys -t $SESSION_NAME:0.1 'echo "╔═══════════════════════════════════════╗"' C-m
tmux send-keys -t $SESSION_NAME:0.1 'echo "║  ПАНЕЛЬ 2: АГЕНТ 1                    ║"' C-m
tmux send-keys -t $SESSION_NAME:0.1 'echo "╚═══════════════════════════════════════╝"' C-m
tmux send-keys -t $SESSION_NAME:0.1 'echo "Статус: ОЖИДАНИЕ"' C-m
tmux send-keys -t $SESSION_NAME:0.1 'echo "IP: [не назначен]"' C-m
tmux send-keys -t $SESSION_NAME:0.1 'echo "Задача: [ожидание]"' C-m

# Панель 2: Агент 2
tmux send-keys -t $SESSION_NAME:0.2 'echo "╔═══════════════════════════════════════╗"' C-m
tmux send-keys -t $SESSION_NAME:0.2 'echo "║  ПАНЕЛЬ 3: АГЕНТ 2                    ║"' C-m
tmux send-keys -t $SESSION_NAME:0.2 'echo "╚═══════════════════════════════════════╝"' C-m
tmux send-keys -t $SESSION_NAME:0.2 'echo "Статус: ОЖИДАНИЕ"' C-m
tmux send-keys -t $SESSION_NAME:0.2 'echo "IP: [не назначен]"' C-m
tmux send-keys -t $SESSION_NAME:0.2 'echo "Задача: [ожидание]"' C-m

# Делаем панель 0 активной
tmux select-pane -t $SESSION_NAME:0.0

# Подключаемся к сессии
tmux attach -t $SESSION_NAME
