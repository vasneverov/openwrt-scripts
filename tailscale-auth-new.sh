#!/bin/bash
# ============================================================
# tailscale-auth-new.sh — авторизация нового роутера в Tailscale
# Использование: ./tailscale-auth-new.sh <ROUTER_IP> <HOSTNAME> [TS_ACCOUNT]
#   ROUTER_IP   — IP роутера в локальной сети (192.168.x.x)
#   HOSTNAME    — имя устройства в Tailscale (например: tr-boss-00, z56-130)
#   TS_ACCOUNT  — номер учётки (1|2|3|4, по умолчанию 4 = n78rout)
#
# Пример:
#   ./tailscale-auth-new.sh 192.168.7.1 tr-boss-00 4
#
# Что делает:
#   1. Создаёт pre-auth key через Tailscale API (одноразовый, preauthorized)
#   2. Заходит на роутер по SSH (провод)
#   3. Выполняет tailscale up --reset с правильными флагами
#   4. Проверяет что точка зеленая
#   5. Проверяет watchdog'ы
# ============================================================

set -e

ROUTER_IP="${1:-}"
HOSTNAME="${2:-}"
TS_ACCOUNT="${3:-4}"

if [ -z "$ROUTER_IP" ] || [ -z "$HOSTNAME" ]; then
    echo "❌ Использование: $0 <ROUTER_IP> <HOSTNAME> [TS_ACCOUNT]"
    echo "   Пример: $0 192.168.7.1 tr-boss-00 4"
    exit 1
fi

SSH_PASS="56756789"
SSH_OPTS="-o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ConnectTimeout=5"

# Маппинг учёток
case "$TS_ACCOUNT" in
    1) TS_TAILNET="vas.neverov@gmail.com"; TS_TOKEN="tskey-api-ktBh42VtRj11CNTRL-RBTDhNJYzdNNqr7wNTfLdNC6PncxBk63B" ;;
    2) TS_TAILNET="ne78va@gmail.com";     TS_TOKEN="tskey-api-kW1ujQ5i2w11CNTRL-wRvm7o2eCkiEfK7M1fhhjiq763ztrBsx" ;;
    3) TS_TAILNET="56papezde@gmail.com";  TS_TOKEN="tskey-api-k7CKy5KXg421CNTRL-UbV7qjoSeKAbB4Akb1VrJAB6NhfpLkYL" ;;
    4) TS_TAILNET="n78rout@gmail.com";    TS_TOKEN="tskey-api-krWQYxzw1511CNTRL-28hSufddDkPy7RxcKzcdjPS24aFRZLh2" ;;
    *) echo "❌ Неизвестная учётка: $TS_ACCOUNT (1-4)"; exit 1 ;;
esac

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Tailscale авторизация"
echo "  Роутер:  $ROUTER_IP"
echo "  Hostname: $HOSTNAME"
echo "  Учётка:  $TS_TAILNET"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ===== Шаг 1: Проверить доступность роутера =====
echo ""
echo "🔍 Шаг 1: Проверка доступности роутера..."
if ! ping -c 2 -W 2 "$ROUTER_IP" >/dev/null 2>&1; then
    echo "❌ Роутер $ROUTER_IP не отвечает на ping"
    exit 1
fi
echo "  ✅ Роутер доступен"

# ===== Шаг 2: Создать pre-auth key =====
echo ""
echo "🔑 Шаг 2: Создание pre-auth key..."
AUTH_KEY=$(curl -s -X POST "https://api.tailscale.com/api/v2/tailnet/$TS_TAILNET/keys" \
    -H "Authorization: Bearer $TS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "capabilities": {
            "devices": {
                "create": {
                    "reusable": false,
                    "ephemeral": false,
                    "preauthorized": true
                }
            }
        }
    }' | grep -o '"key":"[^"]*"' | cut -d'"' -f4)

if [ -z "$AUTH_KEY" ]; then
    echo "❌ Не удалось создать pre-auth key"
    exit 1
fi
echo "  ✅ Pre-auth key создан: ${AUTH_KEY:0:25}..."

# ===== Шаг 3: Авторизация на роутере =====
echo ""
echo "🔗 Шаг 3: Авторизация на роутере..."

# Убить старые tailscale up процессы
sshpass -p "$SSH_PASS" ssh $SSH_OPTS "root@$ROUTER_IP" "
kill \$(ps | grep 'tailscale up' | grep -v grep | awk '{print \$1}') 2>/dev/null || true
" 2>/dev/null || true

# Запустить tailscaled если не запущен
sshpass -p "$SSH_PASS" ssh $SSH_OPTS "root@$ROUTER_IP" "
ps | grep -q 'tailscaled --statedir=' || {
    tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
    sleep 3
}
" 2>/dev/null || true

# Выполнить tailscale up --reset (сбрасывает старые advertise-routes и другие флаги)
# --netfilter-mode=off: tailscale не лезет в iptables (это делает podkop)
# --accept-routes: принимать маршруты от других устройств
# --accept-dns=false: не менять DNS (это делает podkop)
sshpass -p "$SSH_PASS" ssh $SSH_OPTS "root@$ROUTER_IP" "
tailscale up --reset \
    --authkey=$AUTH_KEY \
    --hostname=$HOSTNAME \
    --accept-routes \
    --accept-dns=false \
    --netfilter-mode=off
" 2>&1

echo "  ✅ tailscale up выполнен"

# ===== Шаг 4: Проверить статус =====
echo ""
echo "🟢 Шаг 4: Проверка статуса..."
sleep 3

TS_STATUS=$(sshpass -p "$SSH_PASS" ssh $SSH_OPTS "root@$ROUTER_IP" "tailscale status 2>&1 | head -1" 2>/dev/null)
TS_IP=$(echo "$TS_STATUS" | awk '{print $1}')

if echo "$TS_STATUS" | grep -q "100\."; then
    echo "  ✅ Tailscale авторизован: $TS_IP"
else
    echo "  ⚠️ Статус: $TS_STATUS"
    echo "  ⏳ Ждём 10 сек и проверяем ещё раз..."
    sleep 10
    TS_STATUS=$(sshpass -p "$SSH_PASS" ssh $SSH_OPTS "root@$ROUTER_IP" "tailscale status 2>&1 | head -1" 2>/dev/null)
    TS_IP=$(echo "$TS_STATUS" | awk '{print $1}')
    if echo "$TS_STATUS" | grep -q "100\."; then
        echo "  ✅ Tailscale авторизован: $TS_IP"
    else
        echo "  ❌ Tailscale НЕ авторизовался"
        echo "  Статус: $TS_STATUS"
        exit 1
    fi
fi

# ===== Шаг 5: Проверить watchdog'ы =====
echo ""
echo "🛡️ Шаг 5: Проверка watchdog'ов..."

WATCHDOG_COUNT=$(sshpass -p "$SSH_PASS" ssh $SSH_OPTS "root@$ROUTER_IP" "crontab -l 2>/dev/null | grep -c watchdog" 2>/dev/null || echo "0")
RC_LOCAL_TS=$(sshpass -p "$SSH_PASS" ssh $SSH_OPTS "root@$ROUTER_IP" "grep -c 'tailscaled' /etc/rc.local 2>/dev/null" 2>/dev/null || echo "0")

echo "  Watchdog в cron: $WATCHDOG_COUNT"
echo "  tailscaled в rc.local: $RC_LOCAL_TS"

if [ "$WATCHDOG_COUNT" -lt 1 ]; then
    echo "  ⚠️ Нет watchdog'ов! Рекомендуется установить ts-watchdog.sh"
fi

if [ "$RC_LOCAL_TS" -lt 1 ]; then
    echo "  ⚠️ Нет tailscaled в rc.local! Рекомендуется добавить"
fi

# ===== Шаг 6: Финальная проверка через API =====
echo ""
echo "📡 Шаг 6: Проверка через Tailscale API..."
sleep 5

API_CHECK=$(curl -s "https://api.tailscale.com/api/v2/tailnet/$TS_TAILNET/devices" \
    -H "Authorization: Bearer $TS_TOKEN" | \
    jq ".devices[] | select(.hostname == \"$HOSTNAME\") | {hostname, online, lastSeen}" 2>/dev/null)

if [ -n "$API_CHECK" ]; then
    echo "  ✅ Устройство найдено в Tailscale API:"
    echo "$API_CHECK" | sed 's/^/    /'
else
    echo "  ⚠️ Устройство не найдено в API (возможно ещё не синхронизировалось)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Tailscale авторизация завершена!"
echo "  Роутер: $HOSTNAME ($TS_IP)"
echo "  Учётка: $TS_TAILNET"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
