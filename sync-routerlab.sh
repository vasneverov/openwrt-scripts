#!/bin/bash
# sync-routerlab.sh — двусторонняя синхронизация с GitHub router-lab
# Запускать: bash /Users/vas/CLAUDECODE/sync-routerlab.sh
#
# Как это работает:
# 1. Компьютер (macOS) — основная рабочая станция
# 2. PL5 (91.92.46.229) — сервер за границей, который имеет быстрый доступ к GitHub
# 3. GitHub (vasneverov/router-lab) — центральное хранилище
# 4. Телефон (Termius) — подключается к PL5 и работает с файлами
#
# Синхронизация:
#   Компьютер → PL5 (rsync) → GitHub (git push)
#   GitHub → PL5 (git pull) → Компьютер (rsync)
#
# Использование:
#   bash sync-routerlab.sh              — полная синхронизация
#   bash sync-routerlab.sh status       — только показать статус
#   bash sync-routerlab.sh push         — только отправить изменения на GitHub
#   bash sync-routerlab.sh pull         — только забрать изменения с GitHub

set -e

cd /Users/vas/CLAUDECODE || exit 1

REMOTE="routerlab"
BRANCH="main"
PL5="root@91.92.46.229"
PL5_PASS="6pI3gBvJtVxjea"
PL5_DIR="/root/router-lab"
LOCAL_DIR="/Users/vas/CLAUDECODE"
GIT_TOKEN="github_token_removed"
GIT_REPO="https://vasneverov:${GIT_TOKEN}@github.com/vasneverov/router-lab.git"

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== SYNC router-lab ===${NC}"
echo "Дата: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

status() {
    echo -e "${YELLOW}=== СТАТУС routerlab ===${NC}"
    echo "--- Локальный (компьютер) ---"
    cd "$LOCAL_DIR"
    git status --short | head -20
    echo "---"
    echo "HEAD: $(git rev-parse HEAD | head -c 8)"
    echo ""
    echo "--- PL5 ($PL5) ---"
    sshpass -p "$PL5_PASS" ssh -o StrictHostKeyChecking=no "$PL5" "cd $PL5_DIR && git status --short | head -10 && echo 'HEAD: \$(git rev-parse HEAD | head -c 8)'" 2>/dev/null || echo "PL5 недоступен"
    echo ""
    echo "--- GitHub ---"
    echo "Репозиторий: $GIT_REPO"
    echo "Последний коммит: $(git ls-remote $REMOTE $BRANCH 2>/dev/null | awk '{print $1}' | head -c 8 || echo 'недоступен')"
}

push_to_github() {
    echo -e "${YELLOW}>>> ШАГ 1: Отправка на PL5 (rsync)${NC}"
    sshpass -p "$PL5_PASS" rsync -avz --delete \
        --exclude='.git' --exclude='.DS_Store' --exclude='._*' \
        --exclude='.claude' --exclude='.graphify_*' --exclude='vas.obsidian' \
        --exclude='transcriptions' --exclude='REMOTION' --exclude='cp' --exclude='ls' \
        --exclude='music' --exclude='Скринс' --exclude='router-lab-gitignore' \
        --exclude='*.mp4' --exclude='*.MOV' --exclude='*.mp3' --exclude='*.dmg' \
        --exclude='*.deb' --exclude='*.ass' --exclude='*.srt' \
        --exclude='castdev_analysis.docx' --exclude='graphify-out' \
        --exclude='mita_3.32.0_linux_amd64.deb' \
        --exclude='sing-box-tiny_1.12.22-r1_aarch64_cortex-a53.ipk' \
        --exclude='transcript.txt' --exclude='copy_C7C86959-A7F9-4300-B12B-E0B7397C0DFA.MOV' \
        --exclude='IMG_9075.MOV' \
        "$LOCAL_DIR/" "$PL5:$PL5_DIR/" 2>&1 | tail -3
    echo -e "${GREEN}✓ Файлы отправлены на PL5${NC}"
    echo ""

    echo -e "${YELLOW}>>> ШАГ 2: Коммит и пуш на GitHub с PL5${NC}"
    sshpass -p "$PL5_PASS" ssh -o StrictHostKeyChecking=no "$PL5" "
        cd $PL5_DIR
        git config --global --add safe.directory $PL5_DIR 2>/dev/null
        git add -A
        git commit -m 'sync: \$(date '+%Y-%m-%d %H:%M')' 2>/dev/null || echo 'Нет изменений для коммита'
        git push origin main --force 2>&1
    " 2>&1
    echo -e "${GREEN}✓ Изменения отправлены на GitHub${NC}"
    echo ""

    echo -e "${YELLOW}>>> ШАГ 3: Обновление локального .git-routerlab${NC}"
    sshpass -p "$PL5_PASS" rsync -avz --delete "$PL5:$PL5_DIR/.git/" "$LOCAL_DIR/.git-routerlab/" 2>&1 | tail -1
    cd "$LOCAL_DIR"
    git fetch routerlab-local 2>/dev/null
    git reset --hard routerlab-local/main 2>/dev/null
    echo -e "${GREEN}✓ Локальный репозиторий обновлён${NC}"
}

pull_from_github() {
    echo -e "${YELLOW}>>> ШАГ 1: Pull с GitHub на PL5${NC}"
    sshpass -p "$PL5_PASS" ssh -o StrictHostKeyChecking=no "$PL5" "
        cd $PL5_DIR
        git config --global --add safe.directory $PL5_DIR 2>/dev/null
        git pull origin main --rebase 2>&1 || git fetch origin main 2>&1 && git reset --hard origin/main 2>&1
    " 2>&1
    echo -e "${GREEN}✓ PL5 обновлён с GitHub${NC}"
    echo ""

    echo -e "${YELLOW}>>> ШАГ 2: Копирование с PL5 на компьютер (rsync)${NC}"
    sshpass -p "$PL5_PASS" rsync -avz --delete \
        --exclude='.git' --exclude='.DS_Store' --exclude='._*' \
        --exclude='.claude' --exclude='.graphify_*' --exclude='vas.obsidian' \
        --exclude='transcriptions' --exclude='REMOTION' --exclude='cp' --exclude='ls' \
        --exclude='music' --exclude='Скринс' --exclude='router-lab-gitignore' \
        --exclude='*.mp4' --exclude='*.MOV' --exclude='*.mp3' --exclude='*.dmg' \
        --exclude='*.deb' --exclude='*.ass' --exclude='*.srt' \
        --exclude='castdev_analysis.docx' --exclude='graphify-out' \
        --exclude='mita_3.32.0_linux_amd64.deb' \
        --exclude='sing-box-tiny_1.12.22-r1_aarch64_cortex-a53.ipk' \
        --exclude='transcript.txt' --exclude='copy_C7C86959-A7F9-4300-B12B-E0B7397C0DFA.MOV' \
        --exclude='IMG_9075.MOV' \
        "$PL5:$PL5_DIR/" "$LOCAL_DIR/" 2>&1 | tail -3
    echo -e "${GREEN}✓ Файлы скопированы с PL5 на компьютер${NC}"
    echo ""

    echo -e "${YELLOW}>>> ШАГ 3: Обновление .git-routerlab${NC}"
    sshpass -p "$PL5_PASS" rsync -avz --delete "$PL5:$PL5_DIR/.git/" "$LOCAL_DIR/.git-routerlab/" 2>&1 | tail -1
    cd "$LOCAL_DIR"
    git fetch routerlab-local 2>/dev/null
    git reset --hard routerlab-local/main 2>/dev/null
    echo -e "${GREEN}✓ Локальный репозиторий обновлён${NC}"
}

# Разбор аргументов
case "${1:-}" in
    status)
        status
        exit 0
        ;;
    push)
        push_to_github
        ;;
    pull)
        pull_from_github
        ;;
    "")
        # Полная синхронизация: push + pull
        push_to_github
        echo ""
        echo -e "${GREEN}=== SYNC DONE ===${NC}"
        echo "HEAD: $(cd $LOCAL_DIR && git rev-parse HEAD | head -c 8)"
        ;;
    *)
        echo "Использование:"
        echo "  bash sync-routerlab.sh              — полная синхронизация"
        echo "  bash sync-routerlab.sh status       — только статус"
        echo "  bash sync-routerlab.sh push         — только отправить"
        echo "  bash sync-routerlab.sh pull         — только забрать"
        exit 1
        ;;
esac
