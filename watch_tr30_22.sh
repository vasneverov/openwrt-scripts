#!/bin/bash
# Мониторинг tr30_22 (100.91.90.22) каждые 2 секунды
# Как только роутер доступен — сразу заливаем rescue скрипт

TARGET_IP="100.91.90.22"
RESCUE_SCRIPT="/Users/vas/CLAUDECODE/rescue_tr30_22.sh"
PASS="56756789"
APPLIED=0
SSH_OPTS="-o StrictHostKeyChecking=no -o LogLevel=ERROR -o ConnectTimeout=6"

echo "👁  Мониторинг tr30_22 ($TARGET_IP) каждые 2 сек..."
echo "    Нажми Ctrl+C для остановки"
echo ""

while true; do
    TIMESTAMP=$(date '+%H:%M:%S')

    if sshpass -p "$PASS" ssh $SSH_OPTS root@$TARGET_IP "echo ONLINE" >/dev/null 2>&1; then

        echo "[$TIMESTAMP] ✅ РОУТЕР ОНЛАЙН — заливаю rescue скрипт..."

        # Заливаем и сразу выполняем
        if sshpass -p "$PASS" ssh $SSH_OPTS root@$TARGET_IP "bash -s" < "$RESCUE_SCRIPT" 2>&1; then
            echo ""
            echo "[$TIMESTAMP] ✅✅✅ RESCUE ПРИМЕНЁН УСПЕШНО"
            APPLIED=1
            break
        else
            echo "[$TIMESTAMP] ❌ SSH есть но rescue упал — жду следующего окна..."
        fi

    else
        echo "[$TIMESTAMP] ● оффлайн"
    fi

    sleep 2
done

if [ $APPLIED -eq 1 ]; then
    echo ""
    echo "🎉 tr30_22 стабилизирован. Rescue применён."
fi
