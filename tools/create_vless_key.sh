#!/bin/bash
# create_vless_key.sh — универсальный генератор VLESS-ключа
# Использование: ./create_vless_key.sh <имя_роутера> <город> <страна_выхода>
#
# Пример: ./create_vless_key.sh TR56-13 spb finland
#         ./create_vless_key.sh Z56-94 msk poland
#
# Города: spb (СПб), msk (Москва)
# Страны: finland (Финляндия), poland (Польша), italy (Италия), czech (Чехия)
#
# Делает:
#   1. Генерирует UUID
#   2. Создаёт клиента на целевом сервере через API X-UI
#   3. Перезапускает xray
#   4. Собирает VLESS URL
#   5. Проверяет ключ через check_vless.py
#   6. Если OK — выводит готовый ключ

set -euo pipefail

# ===== КОНФИГУРАЦИЯ =====
# Панели X-UI
declare -A PANELS
PANELS[fin3]="https://144.31.66.115:5050/5050"
PANELS[fin4]="https://45.155.55.198:5050/5050"
PANELS[pl5]="https://91.92.46.229:5050/5050"
PANELS[italy]="https://151.243.198.86:5050/5050"
PANELS[bspb]="https://5.35.84.151:5050/5050"
PANELS[bmsk]="https://159.194.198.172:5050/5050"

# Пароли панелей
declare -A PANEL_PASS
PANEL_PASS[fin3]="Ujkjdf56"
PANEL_PASS[fin4]="Ujkjdf56"
PANEL_PASS[pl5]="Ujkjdf56"
PANEL_PASS[italy]="Ujkjdf56"
PANEL_PASS[bspb]="Ujkjdf56"
PANEL_PASS[bmsk]="Ujkjdf56"

# Relay-схемы: relay_ip:relay_port → target_server:target_inbound_id
# Формат: "relay_ip relay_port target_server target_port pbk sid sni inbound_id"
declare -A RELAYS
RELAYS[spb_finland]="5.35.84.151 4191 fin3 4191 XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw 932e706c www.apple.com 3"
RELAYS[msk_finland]="159.194.198.172 5223 fin4 4191 HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI 4b929012 www.apple.com 1"
RELAYS[msk_poland]="159.194.198.172 5323 pl5 4191 4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw b5023350 www.apple.com 1"
RELAYS[spb_italy]="5.35.84.151 2090 italy 2086 OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI c30f9fec74087d32 www.apple.com 2"
RELAYS[spb_czech]="5.35.84.151 8448 cz2 8448 FyCxYT4Ku_RyR7r2dZYo... dcaa www.apple.com 18"

# Прямые серверы (без relay)
declare -A DIRECTS
DIRECTS[spb_yt]="5.35.84.151 8853 bspb 4 me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM ddcb53b3 www.apple.com"
DIRECTS[msk_yt]="159.194.198.172 8853 bmsk 1 g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI 1cbf0359 www.apple.com"

# ===== ФУНКЦИИ =====

usage() {
    echo "Использование: $0 <имя_роутера> <город> <страна> [--direct]"
    echo ""
    echo "Города: spb, msk"
    echo "Страны: finland, poland, italy, czech, yt"
    echo "--direct  — прямой сервер (без relay)"
    echo ""
    echo "Примеры:"
    echo "  $0 TR56-13 spb finland"
    echo "  $0 Z56-94 msk poland"
    echo "  $0 M56-13 spb yt --direct"
    exit 1
}

gen_uuid() {
    python3 -c "import uuid; print(uuid.uuid4())"
}

xui_login() {
    local panel_url="$1"
    local cookie_file="$2"
    curl -sk -X POST "$panel_url/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"ad","password":"56"}' \
        -c "$cookie_file" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
if not d.get('success'):
    print('LOGIN FAILED')
    sys.exit(1)
" 2>/dev/null
}

xui_add_client() {
    local panel_url="$1"
    local cookie_file="$2"
    local inbound_id="$3"
    local email="$4"
    local uuid="$5"

    # Получаем текущий inbound
    local inbound_json
    inbound_json=$(curl -sk -X GET "$panel_url/panel/api/inbounds/get/$inbound_id" \
        -b "$cookie_file" 2>/dev/null)

    # Добавляем клиента
    python3 -c "
import sys, json

data = json.loads(sys.stdin.read())
if not data.get('success'):
    print('GET INBOUND FAILED')
    sys.exit(1)

obj = data['obj']
settings = json.loads(obj['settings'])
clients = settings.get('clients', [])

# Проверяем, нет ли уже такого email
for c in clients:
    if c.get('email') == '$email':
        print(f'Клиент $email уже существует')
        sys.exit(0)

# Добавляем нового клиента
clients.append({
    'email': '$email',
    'enable': True,
    'expiryTime': 0,
    'id': '$uuid',
    'limitIp': 0,
    'totalGB': 0
})
settings['clients'] = clients
obj['settings'] = json.dumps(settings)

# Отправляем update
import urllib.request, urllib.error
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

payload = json.dumps(obj).encode('utf-8')
req = urllib.request.Request(
    '$panel_url/panel/api/inbounds/update/$inbound_id',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST'
)

# Читаем cookie
cookies = open('$cookie_file').read()
req.add_header('Cookie', cookies.split('\\n')[0].strip())

try:
    resp = urllib.request.urlopen(req, context=ctx)
    result = json.loads(resp.read())
    if result.get('success'):
        print(f'Клиент $email добавлен (UUID: $uuid)')
    else:
        print(f'Ошибка: {result.get(\"msg\")}')
except Exception as e:
    print(f'Ошибка запроса: {e}')
" <<< "$inbound_json"
}

xui_restart_xray() {
    local panel_url="$1"
    local cookie_file="$2"

    curl -sk -X POST "$panel_url/panel/api/server/restartXrayService" \
        -b "$cookie_file" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d.get('success'):
    print('xray перезапущен')
else:
    print('Ошибка перезапуска xray')
" 2>/dev/null
}

build_vless_url() {
    local uuid="$1"
    local relay_ip="$2"
    local relay_port="$3"
    local pbk="$4"
    local sid="$5"
    local sni="$6"
    local name="$7"

    echo "vless://${uuid}@${relay_ip}:${relay_port}?type=grpc&security=reality&mode=gun&serviceName=&pbk=${pbk}&sid=${sid}&sni=${sni}&fp=chrome&spx=%2F#${name}"
}

check_key() {
    local vless_url="$1"
    python3 "$(dirname "$0")/../check_vless.py" "$vless_url" 2>&1 | tail -5
}

# ===== MAIN =====

if [ $# -lt 3 ]; then
    usage
fi

ROUTER_NAME="$1"
CITY="$2"
COUNTRY="$3"
MODE="${4:-relay}"  # relay или direct

# Определяем ключ схемы
if [ "$MODE" = "--direct" ]; then
    SCHEMA_KEY="${CITY}_${COUNTRY}"
    SCHEMA="${DIRECTS[$SCHEMA_KEY]:-}"
    if [ -z "$SCHEMA" ]; then
        echo "Ошибка: нет прямой схемы для ${CITY}_${COUNTRY}"
        echo "Доступные: ${!DIRECTS[*]}"
        exit 1
    fi
    read -r RELAY_IP RELAY_PORT TARGET_SERVER TARGET_INBOUND PBK SID SNI <<< "$SCHEMA"
    RELAY_MODE="direct"
else
    SCHEMA_KEY="${CITY}_${COUNTRY}"
    SCHEMA="${RELAYS[$SCHEMA_KEY]:-}"
    if [ -z "$SCHEMA" ]; then
        echo "Ошибка: нет relay-схемы для ${CITY}_${COUNTRY}"
        echo "Доступные: ${!RELAYS[*]}"
        exit 1
    fi
    read -r RELAY_IP RELAY_PORT TARGET_SERVER TARGET_INBOUND PBK SID SNI <<< "$SCHEMA"
    RELAY_MODE="relay"
fi

PANEL_URL="${PANELS[$TARGET_SERVER]:-}"
PANEL_PASSWORD="${PANEL_PASS[$TARGET_SERVER]:-}"

if [ -z "$PANEL_URL" ]; then
    echo "Ошибка: нет панели для сервера $TARGET_SERVER"
    exit 1
fi

echo "=== Генерация ключа ==="
echo "Роутер: $ROUTER_NAME"
echo "Город: $CITY"
echo "Страна: $COUNTRY"
echo "Режим: $RELAY_MODE"
echo "Relay: ${RELAY_IP}:${RELAY_PORT}"
echo "Цель: $TARGET_SERVER (inbound $TARGET_INBOUND)"
echo ""

# 1. Генерируем UUID
UUID=$(gen_uuid)
echo "UUID: $UUID"

# 2. Создаём клиента на целевом сервере
COOKIE_FILE=$(mktemp)
echo "Логин в панель $TARGET_SERVER..."
xui_login "$PANEL_URL" "$COOKIE_FILE"

echo "Добавление клиента ${ROUTER_NAME}_${TARGET_SERVER}..."
xui_add_client "$PANEL_URL" "$COOKIE_FILE" "$TARGET_INBOUND" "${ROUTER_NAME}_${TARGET_SERVER}" "$UUID"

# 3. Перезапускаем xray
echo "Перезапуск xray..."
xui_restart_xray "$PANEL_URL" "$COOKIE_FILE"
rm -f "$COOKIE_FILE"

# Ждём запуска
sleep 2

# 4. Собираем VLESS URL
VLESS_URL=$(build_vless_url "$UUID" "$RELAY_IP" "$RELAY_PORT" "$PBK" "$SID" "$SNI" "${ROUTER_NAME}_${TARGET_SERVER}")
echo ""
echo "=== VLESS URL ==="
echo "$VLESS_URL"
echo ""

# 5. Проверяем ключ
echo "=== Проверка ключа ==="
CHECK_RESULT=$(check_key "$VLESS_URL")
echo "$CHECK_RESULT"

if echo "$CHECK_RESULT" | grep -q "READY"; then
    echo ""
    echo "✅ КЛЮЧ РАБОЧИЙ — можно ставить на роутер"
    echo ""
    echo "Скопируй строку ниже:"
    echo "──────────────────────────────────────────────"
    echo "$VLESS_URL"
    echo "──────────────────────────────────────────────"
else
    echo ""
    echo "⚠️  КЛЮЧ НЕ ПРОШЁЛ ПРОВЕРКУ — проверь вручную"
    echo "$VLESS_URL"
fi
