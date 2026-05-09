#!/bin/bash
# ============================================================
# check-yt-on-router.sh — проверка podkop на роутере
# Симулирует трафик на YouTube, Telegram, ChatGPT и др.
# Проверяет по обоим профилям (Main + YT)
# ============================================================
# Использование:
#   ./check-yt-on-router.sh <IP роутера> [пароль]
#
# Пример:
#   ./check-yt-on-router.sh 100.113.119.79
#   ./check-yt-on-router.sh 100.87.253.107 56756789
# ============================================================

set -euo pipefail

ROUTER_IP="${1:-}"
PASSWORD="${2:-56756789}"

if [ -z "$ROUTER_IP" ]; then
    echo "❌ Использование: $0 <IP роутера> [пароль]"
    echo "   Пример: $0 100.113.119.79"
    exit 1
fi

SSH_OPTS="-o PreferredAuthentications=password -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o ConnectTimeout=10"

# Список доменов для проверки
# YouTube, Telegram, ChatGPT, Google, GitHub, Cloudflare
DOMAINS=(
    "youtube.com:YouTube"
    "telegram.org:Telegram"
    "chatgpt.com:ChatGPT"
    "google.com:Google"
    "github.com:GitHub"
    "cloudflare.com:Cloudflare"
)

echo "=========================================="
echo "🔍 ПРОВЕРКА PODKOP НА РОУТЕРЕ $ROUTER_IP"
echo "=========================================="
echo ""

# 1. Информация о роутере
HOSTNAME=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" 'cat /proc/sys/kernel/hostname 2>/dev/null || echo "unknown"' 2>/dev/null)
echo "📡 Роутер: $HOSTNAME ($ROUTER_IP)"
echo ""

# 2. Получаем оба профиля
MAIN_PROFILE=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" 'uci get podkop.main.proxy_string 2>/dev/null || echo ""' 2>/dev/null)
YT_PROFILE=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" 'uci show podkop 2>/dev/null | grep -E "^podkop\.(YT|yt)\.proxy_string=" | head -1' 2>/dev/null || echo "")
YT_ENABLED=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" 'uci get podkop.YT.enabled 2>/dev/null || uci get podkop.yt.enabled 2>/dev/null || echo "0"' 2>/dev/null || echo "0")

MAIN_LABEL=$(echo "$MAIN_PROFILE" | grep -oE '#.*' | tr -d '#' | head -c 40)
MAIN_SERVER=$(echo "$MAIN_PROFILE" | grep -oE '@[^:]+:[0-9]+' | head -1)
YT_LABEL=$(echo "$YT_PROFILE" | grep -oE '#.*' | tr -d '#' | head -c 40)
YT_SERVER=$(echo "$YT_PROFILE" | grep -oE '@[^:]+:[0-9]+' | head -1)

echo "━━━ ПРОФИЛИ ━━━"
echo "📌 Main: ${MAIN_LABEL:-не найден}"
echo "   Сервер: ${MAIN_SERVER:-—}"
echo ""
echo "📺 YT:    ${YT_LABEL:-не найден}"
echo "   Сервер: ${YT_SERVER:-—}"
echo "   Статус: $([ "$YT_ENABLED" = "1" ] && echo '✅ включён' || echo '❌ выключен')"
echo ""

# 3. Проверяем, запущен ли podkop
PODKOP_RUNNING=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" 'pidof sing-box 2>/dev/null && echo "running" || echo "stopped"' 2>/dev/null)
echo "⚙️  Podkop (sing-box): $PODKOP_RUNNING"
echo ""

# 4. Функция проверки одного домена
check_domain() {
    local DOMAIN="$1"
    local LABEL="$2"
    local PROFILE_NAME="$3"  # "Main" или "YT"
    
    # Для YT профиля — отключаем Main через uci, чтобы трафик шёл только через YT
    # Но проще: проверяем через curl с явным указанием интерфейса не получится.
    # Podkop в tun-режиме маршрутизирует по правилам — YT профиль только на youtube.com
    # Поэтому для YT проверяем только youtube.com, для Main — всё остальное
    
    local CURL_OPTS="--connect-timeout 8 --max-time 12 -s -o /dev/null -w '%{http_code}|%{time_total}|%{size_download}'"
    
    if [ "$PROFILE_NAME" = "YT" ] && [ "$DOMAIN" != "youtube.com" ]; then
        # YT профиль не должен влиять на другие домены — пропускаем
        echo "—|—|—"
        return
    fi
    
    local RESULT
    RESULT=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" "curl $CURL_OPTS --resolve '' 'https://$DOMAIN' 2>/dev/null || echo '000|0|0'" 2>/dev/null)
    echo "$RESULT"
}

# 5. Проверка Main профиля
echo "━━━ ТЕСТ MAIN ПРОФИЛЯ ━━━"
echo ""
printf "  %-20s │ %-8s │ %-10s │ %-10s │ %s\n" "Сервис" "HTTP" "Время" "Размер" "Статус"
printf "  %s\n" "─────────────────────┼──────────┼────────────┼────────────┼────────────────────"

MAIN_ALL_OK=true
for DOMAIN_ENTRY in "${DOMAINS[@]}"; do
    DOMAIN="${DOMAIN_ENTRY%%:*}"
    LABEL="${DOMAIN_ENTRY##*:}"
    
    RESULT=$(check_domain "$DOMAIN" "$LABEL" "Main")
    HTTP_CODE=$(echo "$RESULT" | cut -d'|' -f1)
    TIME_TOTAL=$(echo "$RESULT" | cut -d'|' -f2)
    SIZE=$(echo "$RESULT" | cut -d'|' -f3)
    
    # 200=OK, 301/302/303=редирект(норма), 403=доступ есть но блокировка ботов(норма)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "303" ] || [ "$HTTP_CODE" = "403" ]; then
        STATUS="✅ OK"
    elif [ "$HTTP_CODE" = "000" ]; then
        STATUS="❌ НЕТ"
        MAIN_ALL_OK=false
    else
        STATUS="⚠️ $HTTP_CODE"
        MAIN_ALL_OK=false
    fi
    
    printf "  %-20s │ %-8s │ %-10s │ %-10s │ %s\n" "$LABEL" "$HTTP_CODE" "${TIME_TOTAL}s" "${SIZE} B" "$STATUS"
done

echo ""
if $MAIN_ALL_OK; then
    echo "  ✅ Main профиль: ВСЕ СЕРВИСЫ РАБОТАЮТ"
else
    echo "  ❌ Main профиль: ЕСТЬ ПРОБЛЕМЫ"
fi
echo ""

# 6. Проверка YT профиля (только youtube.com)
echo "━━━ ТЕСТ YT ПРОФИЛЯ ━━━"
echo ""

if [ "$YT_ENABLED" != "1" ] || [ -z "$YT_PROFILE" ]; then
    echo "  ⏭️  YT профиль выключен или не настроен — пропускаем"
    YT_OK=false
else
    printf "  %-20s │ %-8s │ %-10s │ %-10s │ %s\n" "Сервис" "HTTP" "Время" "Размер" "Статус"
    printf "  %s\n" "─────────────────────┼──────────┼────────────┼────────────┼────────────────────"
    
    RESULT=$(check_domain "youtube.com" "YouTube" "YT")
    HTTP_CODE=$(echo "$RESULT" | cut -d'|' -f1)
    TIME_TOTAL=$(echo "$RESULT" | cut -d'|' -f2)
    SIZE=$(echo "$RESULT" | cut -d'|' -f3)
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "303" ]; then
        STATUS="✅ OK"
        YT_OK=true
    elif [ "$HTTP_CODE" = "000" ]; then
        STATUS="❌ НЕТ"
        YT_OK=false
    else
        STATUS="⚠️ $HTTP_CODE"
        YT_OK=false
    fi
    
    printf "  %-20s │ %-8s │ %-10s │ %-10s │ %s\n" "YouTube" "$HTTP_CODE" "${TIME_TOTAL}s" "${SIZE} B" "$STATUS"
fi
echo ""

# 7. ИТОГ
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 ИТОГ ПРОВЕРКИ"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Main профиль: $($MAIN_ALL_OK && echo '✅ ВСЁ РАБОТАЕТ' || echo '❌ ЕСТЬ ПРОБЛЕМЫ')"
echo "  YT профиль:   $([ "$YT_ENABLED" != "1" ] && echo '⏭️  выключен' || ($YT_OK && echo '✅ РАБОТАЕТ' || echo '❌ НЕ РАБОТАЕТ'))"
echo ""
echo "  📡 Роутер: $HOSTNAME ($ROUTER_IP)"
echo "  ⚙️  Podkop: $PODKOP_RUNNING"
echo ""

if ! $MAIN_ALL_OK; then
    echo "  ❗ Main профиль не работает — проверь ключ"
    echo "     Возможно провайдер блокирует порт ${MAIN_SERVER##*:}"
fi

if [ "$YT_ENABLED" = "1" ] && ! $YT_OK; then
    echo "  ❗ YT профиль не работает — проверь ключ"
    echo "     Возможно провайдер блокирует порт ${YT_SERVER##*:}"
    echo "     Попробуй другой низкий порт на bMSK: 110, 143, 465, 993, 2086, 2087, 2095"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
