#!/bin/bash
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

cd /Users/vas/CLAUDECODE || exit 1

REMOTE="routerlab"
BRANCH="main"

if [ "$1" = "status" ]; then
    echo "=== СТАТУС routerlab ==="
    git remote -v | grep "$REMOTE"
    echo "---"
    git status --short
    echo "---"
    echo "Локальный: $(git rev-parse HEAD | head -c 8)"
    echo "Удалённый: $(git ls-remote $REMOTE $BRANCH 2>/dev/null | awk '{print $1}' | head -c 8)"
    exit 0
fi

echo "=== SYNC router-lab ==="
echo "Дата: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Сначала коммитим локальные изменения (чтобы pull не ругался)
echo ">>> ADD + COMMIT (сохраняем локальные изменения)..."
git add -A
COMMIT_MSG="sync: $(date '+%Y-%m-%d %H:%M')"
git commit -m "$COMMIT_MSG" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Создан коммит: $COMMIT_MSG"
else
    echo "Нет локальных изменений для коммита"
fi
echo ""

# 2. Pull с GitHub (забираем изменения с телефона/PL5)
echo ">>> PULL (забираем изменения с GitHub)..."
git pull $REMOTE $BRANCH --rebase 2>&1
PULL_EXIT=$?
if [ $PULL_EXIT -ne 0 ]; then
    echo "ОШИБКА PULL (код $PULL_EXIT). Возможно конфликт."
    echo "Реши конфликт вручную, затем запусти sync.sh снова."
    exit $PULL_EXIT
fi
echo ""

# 3. Push на GitHub (отправляем объединённые изменения)
echo ">>> PUSH (отправляем на GitHub)..."
git push $REMOTE $BRANCH 2>&1
PUSH_EXIT=$?
if [ $PUSH_EXIT -ne 0 ]; then
    echo "ОШИБКА PUSH (код $PUSH_EXIT)"
    exit $PUSH_EXIT
fi
echo ""

echo "=== SYNC DONE ==="
echo "Локальный коммит: $(git rev-parse HEAD | head -c 8)"
echo "Удалённый коммит: $(git ls-remote $REMOTE $BRANCH 2>/dev/null | awk '{print $1}' | head -c 8)"
