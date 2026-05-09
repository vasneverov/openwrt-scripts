#!/bin/bash
# monitor-reboot.sh — мониторинг времени поднятия роутера после ребута

ROUTER="TR30_05-serebritsa"
START=$(date +%s)

echo "═══════════════════════════════════════════════════════"
echo "  МОНИТОРИНГ ПЕРЕЗАГРУЗКИ $ROUTER"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "[INFO] Старт мониторинга: $(date '+%H:%M:%S')"
echo "[INFO] Чек-интервал: каждые 2 секунды"
echo ""

# Мониторинг
COUNT=0
while [ $COUNT -lt 60 ]; do
    # Пробуем подключиться
    RESULT=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER 'uptime 2>&1' 2>&1)
    ELAPSED=$(($(date +%s) - START))
    
    if echo "$RESULT" | grep -q "up"; then
        # Успех!
        echo ""
        echo "═══════════════════════════════════════════════════════"
        echo "  🟢 РОУТЕР ПОДНЯЛСЯ!"
        echo "═══════════════════════════════════════════════════════"
        echo ""
        echo "[TIME] Время поднятия: ${ELAPSED} секунд"
        echo "[TIME] Начало: $(date -d "@$START" '+%H:%M:%S' 2>/dev/null || date '+%H:%M:%S')"
        echo "[TIME] Конец: $(date '+%H:%M:%S')"
        echo ""
        echo "[INFO] Детали:"
        echo "$RESULT"
        echo ""
        
        # Проверка Tailscale
        echo "[INFO] Проверка Tailscale..."
        TS=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER 'tailscale status | head -1' 2>&1)
        if echo "$TS" | grep -q "100\."; then
            echo "  🟢 Tailscale работает: $TS"
        else
            echo "  🔴 Tailscale не поднялся: $TS"
        fi
        
        # Проверка Podkop
        echo ""
        echo "[INFO] Проверка Podkop..."
        SING=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no root@$ROUTER 'ps | grep sing-box | grep -v grep' 2>&1)
        if [ -n "$SING" ]; then
            echo "  🟢 sing-box работает"
        else
            echo "  🔴 sing-box не запущен"
        fi
        
        echo ""
        echo "═══════════════════════════════════════════════════════"
        echo "  МОНИТОРИНГ ЗАВЕРШЕН"
        echo "═══════════════════════════════════════════════════════"
        break
    else
        COUNT=$((COUNT + 1))
        echo "[INFO] Тик $COUNT (${ELAPSED}с) - роутер ещё не отвечает..."
        sleep 2
    fi
done

if [ $COUNT -ge 60 ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  ❌ ТАЙМАУТ: Роутер не поднялся за 2 минуты"
    echo "═══════════════════════════════════════════════════════"
fi
