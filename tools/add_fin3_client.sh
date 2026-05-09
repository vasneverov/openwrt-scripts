#!/bin/bash
# Быстрое добавление клиента на Fin3 (третья Финляндия) с лимитами 365д/1TB
# Использование: ./add_fin3_client.sh <router_name> <uuid>
# Пример: ./add_fin3_client.sh TR56-99 a1b2c3d4-e5f6-7890-abcd-ef1234567890

ROUTER_NAME="${1:-}"
UUID="${2:-}"

if [ -z "$ROUTER_NAME" ] || [ -z "$UUID" ]; then
    echo "Использование: $0 <router_name> <uuid>"
    echo "Пример: $0 TR56-99 a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    exit 1
fi

# Fin3 параметры
PANEL_URL="https://144.31.66.115:5050/5050"
INBOUND_ID=3
RELAY_IP="5.35.84.151"
RELAY_PORT=4191
PBK="XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw"
SID="932e706c"
SNI="www.apple.com"

# Лимиты: 365 дней + 1 TB
ONE_YEAR_MS=$(($(date +%s) + 365 * 24 * 60 * 60))000
ONE_TB_BYTES=1099511627776

EMAIL="${ROUTER_NAME}_Fin3"

echo "=== Добавление клиента на Fin3 ==="
echo "Роутер: $ROUTER_NAME"
echo "UUID: $UUID"
echo "Email: $EMAIL"
echo "Лимиты: 365 дней / 1 TB"
echo ""

# Создаем payload
SETTINGS=$(cat <<EOF
{"clients":[{"id":"$UUID","email":"$EMAIL","limitIp":0,"enable":true,"expiryTime":$ONE_YEAR_MS,"totalGB":$ONE_TB_BYTES,"tgId":"","subId":"","comment":""}]}
EOF
)

# Логин и получение куки
echo "Логин в панель..."
LOGIN_RESP=$(curl -sk -X POST "$PANEL_URL/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"ad","password":"56"}' \
    -c /tmp/fin3_cookies.txt 2>/dev/null)

if [ ! -f /tmp/fin3_cookies.txt ] || ! grep -q "3x-ui" /tmp/fin3_cookies.txt 2>/dev/null; then
    echo "❌ Ошибка логина"
    exit 1
fi

echo "✅ Логин успешен"

# Проверяем существует ли клиент
echo "Проверка существующего клиента..."
EXISTING=$(curl -sk -b /tmp/fin3_cookies.txt "$PANEL_URL/panel/api/inbounds/get/$INBOUND_ID" 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); clients=json.loads(d.get('obj',{}).get('settings','{}')).get('clients',[]); print([c.get('email') for c in clients if c.get('email') == '$EMAIL'])" 2>/dev/null)

if echo "$EXISTING" | grep -q "$EMAIL"; then
    echo "⚠️ Клиент $EMAIL уже существует"
    echo ""
    echo "=== Готовый ключ ==="
    echo "vless://${UUID}@${RELAY_IP}:${RELAY_PORT}?type=grpc&security=reality&mode=gun&serviceName=&pbk=${PBK}&sid=${SID}&sni=${SNI}&fp=chrome&spx=%2F#${EMAIL}"
    exit 0
fi

# Добавляем клиента
echo "Добавление клиента..."
ADD_RESP=$(curl -sk -b /tmp/fin3_cookies.txt -X POST "$PANEL_URL/panel/api/inbounds/addClient" \
    -H "Content-Type: application/json" \
    -d "{\"id\":$INBOUND_ID,\"settings\":$(echo "$SETTINGS" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}" 2>/dev/null)

if echo "$ADD_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('SUCCESS' if d.get('success') else 'FAIL')" 2>/dev/null | grep -q "SUCCESS"; then
    echo "✅ Клиент добавлен успешно!"
    echo ""
    echo "=== Параметры ==="
    echo "Server: $RELAY_IP:$RELAY_PORT (relay)"
    echo "UUID: $UUID"
    echo "Email: $EMAIL"
    echo "PBK: $PBK"
    echo "SID: $SID"
    echo "SNI: $SNI"
    echo "Expiry: 365 days ($(date -d '+365 days' '+%Y-%m-%d'))"
    echo "Traffic: 1 TB"
    echo ""
    echo "=== Готовый ключ ==="
    echo "vless://${UUID}@${RELAY_IP}:${RELAY_PORT}?type=grpc&security=reality&mode=gun&serviceName=&pbk=${PBK}&sid=${SID}&sni=${SNI}&fp=chrome&spx=%2F#${EMAIL}"
    echo ""
    echo "=== Для подкопа (main) ==="
    echo "vless://${UUID}@${RELAY_IP}:${RELAY_PORT}?type=grpc&security=reality&mode=gun&serviceName=&pbk=${PBK}&sid=${SID}&sni=${SNI}&fp=chrome&spx=%2F#${EMAIL}"
    rm -f /tmp/fin3_cookies.txt
    exit 0
else
    echo "❌ Ошибка добавления клиента"
    echo "Ответ: $ADD_RESP"
    rm -f /tmp/fin3_cookies.txt
    exit 1
fi
