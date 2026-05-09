#!/bin/sh
# podkop-fix-lists.sh — починить обновление community листов podkop
#
# Проблема: провайдер блокирует raw.githubusercontent.com на уровне DPI (SNI).
# Из 4 IP-адресов Fastly CDN (185.199.108-111.133) некоторые могут быть заблокированы.
# Решение: скрипт проверяет каждый IP, добавляет только рабочие в /etc/hosts,
# и запускает podkop list_update.
#
# Использование:
#   sh podkop-fix-lists.sh                  # проверить и починить
#   sh podkop-fix-lists.sh --check-only     # только проверить, не чинить
#   sh podkop-fix-lists.sh --cron           # тихий режим для cron (без цветов)
#
# Совместимость: OpenWrt (ash/busybox), любая версия podkop

set -e

# Цвета (если терминал поддерживает)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; NC=''
fi

info()  { printf "${GREEN}[✓]${NC} %s\n" "$1"; }
warn()  { printf "${YELLOW}[!]${NC} %s\n" "$1"; }
error() { printf "${RED}[✗]${NC} %s\n" "$1"; }
log()   { printf "  %s\n" "$1"; }

# IP-адреса Fastly CDN для raw.githubusercontent.com
# 185.199.108.133 — работает
# 185.199.109.133 — работает
# 185.199.110.133 — может быть заблокирован
# 185.199.111.133 — может быть заблокирован
RAW_IPS="185.199.108.133 185.199.109.133 185.199.110.133 185.199.111.133"
HOSTS_FILE="/etc/hosts"
DOMAIN="raw.githubusercontent.com"
TEST_URL="https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Subnets/IPv4/meta.lst"

# Временный файл для теста
TMP_FILE="/tmp/fix-raw-github-test.$$"

check_only=false
force=false

for arg in "$@"; do
    case "$arg" in
        --check-only) check_only=true ;;
        --force) force=true ;;
    esac
done

echo "=============================================="
echo "  podkop-fix-lists.sh — починить списки podkop"
echo "=============================================="
echo ""

# === ШАГ 1: Проверка DNS ===
echo "--- Шаг 1: DNS резолвинг ---"
DNS_IPS=""
if command -v nslookup >/dev/null 2>&1; then
    DNS_IPS=$(nslookup "$DOMAIN" 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | sort -u | tr '\n' ' ')
elif command -v host >/dev/null 2>&1; then
    DNS_IPS=$(host "$DOMAIN" 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | sort -u | tr '\n' ' ')
fi

if [ -n "$DNS_IPS" ]; then
    info "DNS резолвит $DOMAIN в: $DNS_IPS"
else
    warn "Не удалось получить DNS-записи для $DOMAIN"
fi

# === ШАГ 2: Проверка /etc/hosts ===
echo ""
echo "--- Шаг 2: /etc/hosts ---"
HOSTS_ENTRIES=$(grep -i "$DOMAIN" "$HOSTS_FILE" 2>/dev/null || true)
if [ -n "$HOSTS_ENTRIES" ]; then
    info "Записи в /etc/hosts найдены:"
    echo "$HOSTS_ENTRIES" | while read -r line; do
        log "$line"
    done
else
    warn "/etc/hosts не содержит записей для $DOMAIN"
fi

# === ШАГ 3: Проверка доступности IP ===
echo ""
echo "--- Шаг 3: Проверка доступности IP ---"

WORKING_IPS=""
BROKEN_IPS=""

for ip in $RAW_IPS; do
    if curl -sL --max-time 5 --resolve "$DOMAIN:443:$ip" "$TEST_URL" -o /dev/null -w "%{http_code}" 2>/dev/null | grep -q "200"; then
        WORKING_IPS="$WORKING_IPS $ip"
        info "$ip — доступен"
    else
        BROKEN_IPS="$BROKEN_IPS $ip"
        error "$ip — недоступен"
    fi
done

# === ШАГ 4: Проверка wget (как podkop) ===
echo ""
echo "--- Шаг 4: Проверка wget (как podkop) ---"
if command -v wget >/dev/null 2>&1; then
    if wget -q --timeout=10 "$TEST_URL" -O "$TMP_FILE" 2>/dev/null; then
        SIZE=$(wc -c < "$TMP_FILE" 2>/dev/null || echo "0")
        info "wget: OK ($SIZE байт)"
        rm -f "$TMP_FILE"
    else
        error "wget: не удалось скачать $TEST_URL"
        rm -f "$TMP_FILE" 2>/dev/null
    fi
else
    warn "wget не установлен"
fi

# === ШАГ 5: Исправление /etc/hosts ===
echo ""
echo "--- Шаг 5: Исправление ---"

if [ "$check_only" = true ]; then
    echo ""
    echo "=============================================="
    echo "  РЕЖИМ ТОЛЬКО ПРОВЕРКА"
    echo "=============================================="
    if [ -n "$WORKING_IPS" ]; then
        echo ""
        info "Доступные IP: $WORKING_IPS"
        echo "  Для исправления запустите без --check-only"
    else
        echo ""
        error "Нет доступных IP! Возможно, проблема не в DNS."
    fi
    exit 0
fi

# Удаляем старые записи
if grep -qi "$DOMAIN" "$HOSTS_FILE" 2>/dev/null; then
    warn "Удаляю старые записи $DOMAIN из /etc/hosts"
    sed -i "/$DOMAIN/Id" "$HOSTS_FILE" 2>/dev/null || \
        sed -i '' "/$DOMAIN/Id" "$HOSTS_FILE" 2>/dev/null || {
        # fallback для busybox (OpenWrt)
        grep -v -i "$DOMAIN" "$HOSTS_FILE" > "$HOSTS_FILE.tmp" && \
        mv "$HOSTS_FILE.tmp" "$HOSTS_FILE"
    }
fi

# Добавляем только рабочие IP
COUNT=0
for ip in $WORKING_IPS; do
    echo "$ip $DOMAIN" >> "$HOSTS_FILE"
    COUNT=$((COUNT + 1))
done

if [ "$COUNT" -gt 0 ]; then
    info "Добавлено $COUNT рабочих IP в /etc/hosts"
else
    # Если ни один IP не работает — добавляем все, может временная проблема
    warn "Ни один IP не работает! Добавляю все IP на всякий случай."
    for ip in $RAW_IPS; do
        echo "$ip $DOMAIN" >> "$HOSTS_FILE"
    done
fi

# === ШАГ 6: Проверка после исправления ===
echo ""
echo "--- Шаг 6: Проверка после исправления ---"
if curl -sL --max-time 10 "$TEST_URL" -o /dev/null -w "%{http_code}" 2>/dev/null | grep -q "200"; then
    info "curl: OK — $DOMAIN доступен"
else
    error "curl: $DOMAIN всё ещё недоступен"
fi

if command -v wget >/dev/null 2>&1; then
    if wget -q --timeout=10 "$TEST_URL" -O "$TMP_FILE" 2>/dev/null; then
        SIZE=$(wc -c < "$TMP_FILE" 2>/dev/null || echo "0")
        info "wget: OK ($SIZE байт)"
        rm -f "$TMP_FILE"
    else
        error "wget: не удалось скачать $TEST_URL"
        rm -f "$TMP_FILE" 2>/dev/null
    fi
fi

# === ШАГ 7: Запуск обновления podkop ===
echo ""
echo "--- Шаг 7: Обновление podkop ---"
if command -v /usr/bin/podkop >/dev/null 2>&1; then
    info "Запускаю podkop list_update..."
    /usr/bin/podkop list_update 2>&1 || warn "podkop list_update завершился с ошибкой"
else
    warn "podkop не найден"
fi

echo ""
echo "=============================================="
echo "  ГОТОВО"
echo "=============================================="
echo ""
echo "Итоговые записи в /etc/hosts:"
grep -i "$DOMAIN" "$HOSTS_FILE" 2>/dev/null || echo "(нет записей)"
echo ""
echo "Для автоматического запуска добавьте в cron:"
echo "  0 3 * * * /bin/sh /root/podkop-fix-lists.sh --cron"
