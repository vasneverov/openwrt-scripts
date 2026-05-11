#!/bin/sh
# Универсальный спасительный скрипт
# Применяется через SSH, НЕ перезагружает Tailscale, НЕ перезапускает podkop
# Только фиксы + 3 watchdog'а на 2 минуты
#
# Запуск: cat rescue_generic.sh | ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@100.103.95.72 sh -s
#
# Железное правило: Tailscale НЕ ТРОГАЕМ, ничего НЕ ПЕРЕЗАГРУЖАЕМ

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   УНИВЕРСАЛЬНЫЙ СПАСИТЕЛЬНЫЙ СКРИПТ             ║"
echo "║   Tailscale НЕ ТРОГАЕМ • Podkop НЕ РЕСТАРТИМ    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ===== 1. Tailscale fw_mode = none =====
echo "[1/9] Tailscale fw_mode → none"
CURRENT_FW=$(uci get tailscale.settings.fw_mode 2>/dev/null)
if [ "$CURRENT_FW" != "none" ]; then
    uci set tailscale.settings.fw_mode='none'
    uci commit tailscale
    echo "  ✓ fw_mode: $CURRENT_FW → none"
else
    echo "  ✓ fw_mode уже none"
fi

# ===== 2. init.d/tailscale DISABLED =====
echo "[2/9] init.d/tailscale → DISABLED"
if /etc/init.d/tailscale enabled 2>/dev/null; then
    /etc/init.d/tailscale disable
    echo "  ✓ init.d/tailscale disabled"
else
    echo "  ✓ init.d/tailscale уже disabled"
fi

# ===== 3. WAN ifname (podkop использует ifname, а не device) =====
echo "[3/9] WAN ifname → проверка"
WAN_IFNAME=$(uci get network.wan.ifname 2>/dev/null)
if [ -z "$WAN_IFNAME" ]; then
    WAN_DEVICE=$(uci get network.wan.device 2>/dev/null)
    if [ -n "$WAN_DEVICE" ]; then
        uci set network.wan.ifname="$WAN_DEVICE"
        uci commit network
        echo "  ✓ network.wan.ifname=$WAN_DEVICE (добавлен из device)"
    else
        echo "  ⚠️ WAN device не найден, пропускаем"
    fi
else
    echo "  ✓ network.wan.ifname=$WAN_IFNAME (уже есть)"
fi

# ===== 4. exclude_ntp = 1 + enable_output_network_interface = 1 =====
echo "[4/9] Podkop exclude_ntp → 1"
CURRENT_NTP=$(uci get podkop.settings.exclude_ntp 2>/dev/null)
if [ "$CURRENT_NTP" != "1" ]; then
    uci set podkop.settings.exclude_ntp='1'
    echo "  ✓ exclude_ntp: $CURRENT_NTP → 1"
else
    echo "  ✓ exclude_ntp уже 1"
fi

echo "      enable_output_network_interface → 1"
CURRENT_OUTPUT=$(uci get podkop.settings.enable_output_network_interface 2>/dev/null)
if [ "$CURRENT_OUTPUT" != "1" ]; then
    uci set podkop.settings.enable_output_network_interface='1'
    echo "  ✓ enable_output_network_interface: $CURRENT_OUTPUT → 1"
else
    echo "  ✓ enable_output_network_interface уже 1"
fi
uci commit podkop

# ===== 5. rc.local — минимальный + watchdog в фоне =====
echo "[5/9] rc.local → проверка/создание"
if [ -f /etc/rc.local ] && grep -q "ts-watchdog.sh &" /etc/rc.local 2>/dev/null; then
    echo "  ✓ rc.local уже новый (минимальный + watchdog в фоне)"
else
    [ -f /etc/rc.local ] && cp /etc/rc.local /etc/rc.local.bak 2>/dev/null
    
    cat > /etc/rc.local << 'EOF'
#!/bin/sh

# === TAILSCALE STARTUP ===
tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
sleep 3
tailscale up --accept-dns=false --accept-routes &

# === WATCHDOG В ФОНЕ ===
# Ждёт tailscale до 120 сек, перезапускает если упал
/etc/ts-watchdog.sh &

logger -t rc.local 'rc.local complete'
exit 0
EOF
    chmod +x /etc/rc.local
    echo "  ✓ rc.local создан (минимальный + watchdog в фоне)"
fi


# ===== 6. firewall → tailscale0 в LAN зону =====
# ВАЖНО: НЕ перезагружаем firewall! fw4 (nftables) сбросит правила Tailscale.
# Просто сохраняем конфиг — tailscale0 добавится при следующей перезагрузке.
echo "[6/9] firewall → tailscale0 в LAN зону"
CURRENT_DEV=$(uci get firewall.@zone[0].device 2>/dev/null)
if echo "$CURRENT_DEV" | grep -q "tailscale0"; then
    echo "  ✓ tailscale0 уже в LAN зоне"
else
    uci set firewall.@zone[0].device='br-lan tailscale0' 2>/dev/null
    uci commit firewall 2>/dev/null
    echo "  ✓ tailscale0 добавлен в LAN зону (конфиг сохранён, firewall НЕ перезагружен)"
fi

# ===== 7. Три watchdog'а на 2 минуты =====
echo "[7/9] Watchdog'ы (3 шт, каждая 2 мин)..."

# 5a. Tailscale watchdog v3.1 — единый, с lock-файлом + NoState fix
cat > /etc/ts-watchdog.sh << 'WEOF'
#!/bin/sh

# === ts-watchdog v3.1 ===
# Единый watchdog: работает и из rc.local, и из крона
# Lock-файл: не запускается дважды
# Не убивает tailscale если он уже онлайн
# NoState fix: если tailscale status выдаёт NoState — killall tailscaled + запуск заново

LOCKFILE=/tmp/ts-watchdog.lock

# Lock-файл: если уже запущен — выходим
if [ -f "$LOCKFILE" ]; then
    LOCKPID=$(cat "$LOCKFILE" 2>/dev/null)
    if kill -0 "$LOCKPID" 2>/dev/null; then
        exit 0
    fi
fi
echo $$ > "$LOCKFILE"

# 1. Проверка tailscaled процесс
if ! ps | grep -q "tailscaled --state="; then
    logger -t ts-watchdog "tailscaled not running, restarting..."
    tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
    sleep 5
    tailscale up --accept-dns=false --accept-routes &
    logger -t ts-watchdog "tailscaled restarted"
    rm -f "$LOCKFILE"
    exit 0
fi

# 2. Проверка что tailscale онлайн
TS_STATUS=$(tailscale status 2>&1)

# 2a. Если tailscaled в битом состоянии (NoState) — перезапускаем целиком
if echo "$TS_STATUS" | grep -q "NoState"; then
    logger -t ts-watchdog "tailscaled in NoState (DERP lost), full restart..."
    killall tailscale 2>/dev/null
    sleep 1
    killall tailscaled 2>/dev/null
    sleep 2
    tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
    sleep 5
    date +%s > /tmp/ts-up-start
    tailscale up --accept-dns=false --accept-routes &
    logger -t ts-watchdog "tailscaled fully restarted (NoState fix)"
    rm -f "$LOCKFILE"
    exit 0
fi

# 2b. Нормальный онлайн
if echo "$TS_STATUS" | grep -q '100\.'; then
    # ✅ Tailscale онлайн — ничего не делаем
    # Применяем podkop-fw4-fix если нужно
    if [ -x /root/podkop-fw4-fix.sh ]; then
        /root/podkop-fw4-fix.sh update 2>/dev/null
    fi
    rm -f "$LOCKFILE"
    exit 0
fi

# 3. Tailscale НЕ онлайн — пробуем перезапустить
logger -t ts-watchdog "tailscale not online, reconnecting..."

# Проверяем не висит ли tailscale up
TS_UP_PID=$(ps | grep "tailscale up" | grep -v grep | awk '{print $1}')
if [ -n "$TS_UP_PID" ]; then
    # Если tailscale up висит больше 90 сек — убиваем
    # 30 сек мало — tailscale up может висеть 40-50 сек при первом запуске
    if [ -f /tmp/ts-up-start ] && [ $(($(date +%s) - $(cat /tmp/ts-up-start))) -gt 90 ]; then
        logger -t ts-watchdog "tailscale up stuck (PID $TS_UP_PID), killing..."
        kill "$TS_UP_PID" 2>/dev/null
        sleep 2
        date +%s > /tmp/ts-up-start
        tailscale up --accept-dns=false --accept-routes &
        logger -t ts-watchdog "tailscale up restarted"
    fi
else
    # tailscale up не запущен — запускаем
    date +%s > /tmp/ts-up-start
    tailscale up --accept-dns=false --accept-routes &
    logger -t ts-watchdog "tailscale up started"
fi

rm -f "$LOCKFILE"
WEOF
chmod +x /etc/ts-watchdog.sh
echo "  ✓ ts-watchdog.sh v3.1 (NoState fix + lock-файл)"


# 5b. Podkop watchdog
cat > /etc/podkop-watchdog.sh << 'WEOF'
#!/bin/sh
if ! ps | grep -q "sing-box run"; then
    logger -t podkop-watchdog "sing-box not running, restarting podkop"
    /etc/init.d/podkop restart
fi
WEOF
chmod +x /etc/podkop-watchdog.sh
echo "  ✓ podkop-watchdog.sh"

# 5c. Route watchdog
cat > /etc/route-watchdog.sh << 'WEOF'
#!/bin/sh
nft list table inet PodkopTable >/dev/null 2>&1 || {
    logger -t route-watchdog "PodkopTable missing, restarting podkop"
    /etc/init.d/podkop restart
}
WEOF
chmod +x /etc/route-watchdog.sh
echo "  ✓ route-watchdog.sh"

# ===== 8. Crontab =====
echo "[8/9] Crontab → 3 watchdog'а + обновление списков"
(
    crontab -l 2>/dev/null | grep -v -E "(ts-watchdog|podkop-watchdog|route-watchdog|list_update)"
    echo "*/2 * * * * /etc/ts-watchdog.sh"
    echo "*/2 * * * * /etc/podkop-watchdog.sh"
    echo "*/2 * * * * /etc/route-watchdog.sh"
    echo "13 */3 * * * /usr/bin/podkop list_update"
) | crontab -
echo "  ✓ crontab обновлён"

# ===== 9. check-ip скрипт диагностики =====
echo "[9/9] check-ip → скрипт диагностики"
cat > /usr/bin/check-ip << 'CIPEOF'
#!/bin/sh
echo '╔══════════════════════════════════════════════╗'
echo '║              CHECK-IP                        ║'
echo '║  Проверка IP через прокси и напрямую        ║'
echo '╚══════════════════════════════════════════════╝'
echo ''
echo '=== ЧЕРЕЗ ПРОКСИ (как LAN-клиент) ==='
echo '--- cloudflare.com/cdn-cgi/trace ---'
curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -E 'ip=|loc='
echo '--- ident.me ---'
curl -s --connect-timeout 5 --max-time 10 https://ident.me 2>/dev/null
echo ''
echo '=== НАПРЯМУЮ (с роутера) ==='
echo '--- ipinfo.io ---'
curl -s --connect-timeout 5 --max-time 10 https://ipinfo.io/json 2>/dev/null | grep -E '\"ip\"|\"country\"|\"city\"'
echo '--- ifconfig.me ---'
curl -s --connect-timeout 5 --max-time 10 https://ifconfig.me 2>/dev/null
echo ''
echo '=== ТЕСТЫ САЙТОВ ==='
for url in google.com youtube.com telegram.org facebook.com instagram.com rutracker.org tiktok.com x.com discord.com github.com; do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://$url 2>/dev/null)
  TIME=$(curl -s -o /dev/null -w '%{time_total}' --max-time 8 https://$url 2>/dev/null)
  printf '%-15s %3s  (%ss)\n' "$url" "$CODE" "$TIME"
done
CIPEOF
chmod +x /usr/bin/check-ip
echo "  ✓ /usr/bin/check-ip создан"

# ===== ФИНАЛ =====
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ СПАСЕНИЕ ПРИМЕНЕНО                           ║"
echo "║                                                  ║"
echo "║  Tailscale: НЕ ТРОГАЛИ (сохранён)               ║"
echo "║  Podkop: НЕ РЕСТАРТИЛИ (сохранён)               ║"
echo "║  Перезагрузка: НЕ ДЕЛАЛИ                         ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Проверка:"
echo "  fw_mode:      $(uci get tailscale.settings.fw_mode)"
echo "  exclude_ntp:  $(uci get podkop.settings.exclude_ntp)"
echo "  init.d:       $(/etc/init.d/tailscale enabled 2>/dev/null && echo 'ENABLED' || echo 'DISABLED')"
echo "  watchdog:     $(crontab -l | grep -c watchdog) записи"
echo "  tailscaled:   $(ps | grep 'tailscaled --state=' | grep -v grep | head -1 | awk '{print $NF}')"
echo "  check-ip:     $(which check-ip 2>/dev/null || echo 'НЕ НАЙДЕН')"
echo ""
echo "Для проверки IP выполните: check-ip"
echo ""
