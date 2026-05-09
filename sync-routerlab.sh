#!/bin/bash
# =============================================================================
# sync-routerlab.sh — синхронизация с GitHub для PL5
# Запускать: bash /root/router-lab/sync-routerlab.sh
# =============================================================================

cd /root/router-lab || exit 1

REMOTE=origin
BRANCH=main

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

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

echo ""
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo -e "${BOLD}${CYAN}  🔄 СИНХРОНИЗАЦИЯ PL5 → GitHub${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo -e "  ${DIM}Дата:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "  ${DIM}Сервер:${NC} PL5 (91.92.46.229)"
echo ""

# Статус до
echo -e "${BOLD}Статус до синхронизации:${NC}"
LOCAL_HASH=$(git rev-parse HEAD | head -c 8)
REMOTE_HASH=$(git ls-remote $REMOTE $BRANCH 2>/dev/null | awk '{print $1}' | head -c 8)
echo -e "  ${DIM}Локальный:${NC} ${GREEN}${LOCAL_HASH}${NC}"
echo -e "  ${DIM}GitHub:${NC}    ${CYAN}${REMOTE_HASH:-(недоступен)}${NC}"
CHANGES=$(git status --short | wc -l | tr -d ' ')
if [ "$CHANGES" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠ Локальные изменения: $CHANGES файлов${NC}"
fi
echo ""

# Pull
echo -e "${BOLD}${YELLOW}📥 Pull с GitHub${NC}"
progress_bar 0 4 "Fetch..."
git fetch $REMOTE $BRANCH 2>&1
progress_bar 2 4 "Pull..."
git pull $REMOTE $BRANCH --rebase 2>&1
progress_bar 4 4 "Готово"
echo ""

# Commit + Push
echo -e "${BOLD}${YELLOW}📤 Push на GitHub${NC}"
progress_bar 0 4 "Add..."
git add -A
progress_bar 1 4 "Commit..."
git commit -m "pl5: sync $(date '+%Y-%m-%d %H:%M')" 2>/dev/null || echo -e "  ${DIM}Нет изменений${NC}"
progress_bar 3 4 "Push..."
git push $REMOTE $BRANCH --force 2>&1
progress_bar 4 4 "Готово"
echo ""

# Статус после
echo -e "${BOLD}Результат:${NC}"
NEW_HASH=$(git rev-parse HEAD | head -c 8)
REMOTE_HASH=$(git ls-remote $REMOTE $BRANCH 2>/dev/null | awk '{print $1}' | head -c 8)
echo -e "  ${DIM}Локальный:${NC} ${GREEN}${NEW_HASH}${NC}"
echo -e "  ${DIM}GitHub:${NC}    ${CYAN}${REMOTE_HASH:-(недоступен)}${NC}"

if [ "$NEW_HASH" = "$REMOTE_HASH" ]; then
    echo -e "  ${GREEN}✅ Синхронизация завершена${NC}"
else
    echo -e "  ${RED}⚠ Хэши не совпадают${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo ""
