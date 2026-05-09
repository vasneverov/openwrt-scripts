#!/bin/bash
# =============================================================================
# sync-routerlab.sh — двусторонняя синхронизация с GitHub router-lab
# Запускать: bash /Users/vas/CLAUDECODE/sync-routerlab.sh
#
# Что делает:
# 1. Pull с GitHub (забирает изменения, сделанные с телефона/PL5)
# 2. Commit локальных изменений (сделанных с компьютера)
# 3. Push на GitHub (чтобы PL5/телефон видели изменения)
#
# Использование:
#   bash sync-routerlab.sh          — полная синхронизация
#   bash sync-routerlab.sh status   — только показать статус
#   bash sync-routerlab.sh pull     — только pull (забрать с GitHub)
#   bash sync-routerlab.sh push     — только push (отправить на GitHub)
#   bash sync-routerlab.sh auto     — автосинхронизация (pull + push, без лишнего вывода)
# =============================================================================

cd /Users/vas/CLAUDECODE || exit 1

REMOTE="routerlab"
BRANCH="main"

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# Функция: автосинхронизация (тихая, для вызова при старте сессии)
auto_sync() {
    local has_changes=false
    
    # Pull
    git fetch $REMOTE $BRANCH 2>/dev/null
    LOCAL=$(git rev-parse HEAD 2>/dev/null)
    REMOTE_HASH=$(git rev-parse FETCH_HEAD 2>/dev/null)
    
    if [ "$LOCAL" != "$REMOTE_HASH" ] && [ -n "$REMOTE_HASH" ]; then
        has_changes=true
        echo -e "${CYAN}📡 Обнаружены изменения на GitHub. Синхронизирую...${NC}"
        git pull $REMOTE $BRANCH --rebase 2>/dev/null || git pull $REMOTE $BRANCH 2>/dev/null
        echo -e "${GREEN}✓ Синхронизировано. HEAD: $(git rev-parse HEAD | head -c 8)${NC}"
    fi
    
    # Commit + Push локальных изменений
    if [ -n "$(git status --short)" ]; then
        has_changes=true
        git add -A
        git commit -m "sync: auto $(date '+%Y-%m-%d %H:%M')" 2>/dev/null
        git push $REMOTE $BRANCH 2>/dev/null
        echo -e "${GREEN}✓ Локальные изменения отправлены на GitHub. HEAD: $(git rev-parse HEAD | head -c 8)${NC}"
    fi
    
    if [ "$has_changes" = false ]; then
        echo -e "${GREEN}✓ Всё синхронизировано. HEAD: $(git rev-parse HEAD | head -c 8)${NC}"
    fi
}

# Функция: прогресс-бар
progress_bar() {
    local current=$1
    local total=$2
    local label=$3
    local width=40
    local pct=$((current * 100 / total))
    local filled=$((pct * width / 100))
    local empty=$((width - filled))
    
    printf "${CYAN}[${NC}"
    printf "${GREEN}%${filled}s${NC}" | tr ' ' '█'
    printf "${DIM}%${empty}s${NC}" | tr ' ' '░'
    printf "${CYAN}]${NC} ${BOLD}%3d%%${NC} ${DIM}%s${NC}\n" "$pct" "$label"
}

# Функция: показать статус с визуализацией
show_status() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  📡 СТАТУС СИНХРОНИЗАЦИИ router-lab${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo ""
    
    # Дата
    echo -e "  ${DIM}Дата:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 1. Локальный (компьютер)
    LOCAL_HASH=$(git rev-parse HEAD 2>/dev/null | head -c 8)
    LOCAL_MSG=$(git log --oneline -1 2>/dev/null | head -c 60)
    LOCAL_CHANGES=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
    
    echo -e "  ${BOLD}💻 ЛОКАЛЬНЫЙ (компьютер)${NC}"
    echo -e "    ${DIM}HEAD:${NC}     ${GREEN}${LOCAL_HASH}${NC} ${DIM}${LOCAL_MSG}${NC}"
    if [ "$LOCAL_CHANGES" -gt 0 ]; then
        echo -e "    ${YELLOW}⚠ Изменения: ${LOCAL_CHANGES} файлов не закоммичены${NC}"
        git status --short 2>/dev/null | head -5 | while read line; do
            echo -e "    ${DIM}   ${line}${NC}"
        done
    else
        echo -e "    ${GREEN}✓ Чисто, изменений нет${NC}"
    fi
    echo ""
    
    # 2. GitHub (удалённый)
    echo -e "  ${BOLD}☁️  GITHUB (vasneverov/router-lab)${NC}"
    REMOTE_HASH=$(git ls-remote $REMOTE $BRANCH 2>/dev/null | awk '{print $1}' | head -c 8)
    if [ -n "$REMOTE_HASH" ]; then
        echo -e "    ${DIM}HEAD:${NC}     ${CYAN}${REMOTE_HASH}${NC}"
        if [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
            echo -e "    ${GREEN}✓ Синхронизировано${NC}"
        else
            echo -e "    ${YELLOW}⚠ Расходятся! Локальный: ${LOCAL_HASH} ≠ GitHub: ${REMOTE_HASH}${NC}"
        fi
    else
        echo -e "    ${RED}✗ Недоступен${NC}"
    fi
    echo ""
    
    # 3. PL5 (сервер)
    echo -e "  ${BOLD}🌐 PL5 (91.92.46.229)${NC}"
    PL5_HASH=$(sshpass -p '6pI3gBvJtVxjea' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@91.92.46.229 "cd /root/router-lab && git rev-parse HEAD 2>/dev/null | head -c 8" 2>/dev/null)
    if [ -n "$PL5_HASH" ]; then
        echo -e "    ${DIM}HEAD:${NC}     ${CYAN}${PL5_HASH}${NC}"
        if [ "$REMOTE_HASH" = "$PL5_HASH" ]; then
            echo -e "    ${GREEN}✓ Синхронизирован с GitHub${NC}"
        else
            echo -e "    ${YELLOW}⚠ Расходится с GitHub!${NC}"
        fi
    else
        echo -e "    ${RED}✗ Недоступен (проверь Tailscale/SSH)${NC}"
    fi
    echo ""
    
    # Сводка
    echo -e "${CYAN}───────────────────────────────────────────${NC}"
    if [ "$LOCAL_HASH" = "$REMOTE_HASH" ] && [ "$REMOTE_HASH" = "$PL5_HASH" ]; then
        echo -e "  ${GREEN}${BOLD}✅ ПОЛНАЯ СИНХРОНИЗАЦИЯ: Компьютер = GitHub = PL5${NC}"
    else
        echo -e "  ${YELLOW}${BOLD}⚠ НЕОБХОДИМА СИНХРОНИЗАЦИЯ${NC}"
        echo -e "  ${DIM}Запусти: bash sync-routerlab.sh${NC}"
    fi
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo ""
}

# Функция: pull с GitHub
do_pull() {
    echo -e "${YELLOW}>>> PULL (забираем изменения с GitHub)...${NC}"
    progress_bar 0 4 "Подготовка..."
    
    git fetch $REMOTE $BRANCH 2>&1
    progress_bar 1 4 "Fetch с GitHub..."
    
    REMOTE_HASH=$(git rev-parse FETCH_HEAD 2>/dev/null | head -c 8)
    LOCAL_HASH=$(git rev-parse HEAD 2>/dev/null | head -c 8)
    
    if [ "$REMOTE_HASH" != "$LOCAL_HASH" ]; then
        echo -e "  ${DIM}Новые коммиты на GitHub:${NC}"
        git log --oneline HEAD..FETCH_HEAD 2>/dev/null | head -5
        echo ""
    fi
    
    git pull $REMOTE $BRANCH --rebase 2>&1
    PULL_EXIT=$?
    progress_bar 3 4 "Pull..."
    
    if [ $PULL_EXIT -ne 0 ]; then
        echo -e "${RED}ОШИБКА PULL (код $PULL_EXIT). Возможно конфликт.${NC}"
        echo -e "${YELLOW}Реши конфликт вручную, затем запусти sync.sh снова.${NC}"
        return $PULL_EXIT
    fi
    
    NEW_HASH=$(git rev-parse HEAD | head -c 8)
    progress_bar 4 4 "Готово"
    echo ""
    echo -e "${GREEN}✓ Pull завершён. HEAD: ${NEW_HASH}${NC}"
    return 0
}

# Функция: push на GitHub
do_push() {
    echo -e "${YELLOW}>>> PUSH (отправляем на GitHub)...${NC}"
    progress_bar 0 4 "Подготовка..."
    
    # Сначала коммитим
    git add -A
    COMMIT_MSG="sync: $(date '+%Y-%m-%d %H:%M')"
    git commit -m "$COMMIT_MSG" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Создан коммит: ${COMMIT_MSG}${NC}"
    else
        echo -e "  ${DIM}Нет локальных изменений для коммита${NC}"
    fi
    progress_bar 2 4 "Commit..."
    
    # Push
    git push $REMOTE $BRANCH 2>&1
    PUSH_EXIT=$?
    progress_bar 3 4 "Push..."
    
    if [ $PUSH_EXIT -ne 0 ]; then
        echo -e "${RED}ОШИБКА PUSH (код $PUSH_EXIT)${NC}"
        return $PUSH_EXIT
    fi
    
    NEW_HASH=$(git rev-parse HEAD | head -c 8)
    progress_bar 4 4 "Готово"
    echo ""
    echo -e "${GREEN}✓ Push завершён. HEAD: ${NEW_HASH}${NC}"
    return 0
}

# Функция: полная синхронизация
do_sync() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  🔄 СИНХРОНИЗАЦИЯ router-lab${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo -e "  ${DIM}Дата:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Шаг 1: Pull
    echo -e "${BOLD}${YELLOW}📥 Шаг 1/3: Забираем изменения с GitHub${NC}"
    do_pull || return $?
    echo ""
    
    # Шаг 2: Push
    echo -e "${BOLD}${YELLOW}📤 Шаг 2/3: Отправляем локальные изменения${NC}"
    do_push || return $?
    echo ""
    
    # Шаг 3: Проверка
    echo -e "${BOLD}${YELLOW}✅ Шаг 3/3: Проверка синхронизации${NC}"
    LOCAL_HASH=$(git rev-parse HEAD | head -c 8)
    REMOTE_HASH=$(git ls-remote $REMOTE $BRANCH 2>/dev/null | awk '{print $1}' | head -c 8)
    
    progress_bar 0 3 "Проверка..."
    sleep 1
    progress_bar 1 3 "Сравнение..."
    sleep 1
    progress_bar 3 3 "Готово"
    
    echo ""
    if [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
        echo -e "${GREEN}${BOLD}✅ СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА${NC}"
        echo -e "  ${DIM}Локальный:${NC} ${GREEN}${LOCAL_HASH}${NC}"
        echo -e "  ${DIM}GitHub:${NC}    ${GREEN}${REMOTE_HASH}${NC}"
    else
        echo -e "${RED}${BOLD}⚠ ОШИБКА: Хэши не совпадают${NC}"
        echo -e "  ${DIM}Локальный:${NC} ${LOCAL_HASH}"
        echo -e "  ${DIM}GitHub:${NC}    ${REMOTE_HASH}"
    fi
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo ""
}

# Главная логика
case "${1:-sync}" in
    status)
        show_status
        ;;
    pull)
        do_pull
        ;;
    push)
        do_push
        ;;
    auto)
        auto_sync
        ;;
    sync|"")
        do_sync
        ;;
    *)
        echo -e "${YELLOW}Использование:${NC}"
        echo "  bash sync-routerlab.sh          — полная синхронизация"
        echo "  bash sync-routerlab.sh status   — показать статус"
        echo "  bash sync-routerlab.sh pull     — только pull"
        echo "  bash sync-routerlab.sh push     — только push"
        echo "  bash sync-routerlab.sh auto     — автосинхронизация (тихая)"
        ;;
esac
