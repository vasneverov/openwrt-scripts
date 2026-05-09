#!/bin/sh
# =============================================================================
# УНИВЕРСАЛЬНЫЙ СПАСИТЕЛЬНЫЙ СКРИПТ — Tailscale + Podkop + OpenWrt
# =============================================================================
# Применяется через SSH (Tailscale/Anydesk), НЕ перезагружает Tailscale,
# НЕ перезапускает podkop, НЕ ребутит роутер.
#
# Запуск:
#   sh <(wget -O - https://raw.githubusercontent.com/vasneverov/openwrt-fix/main/fix-tailscale-openwrt.sh)
#
# Или через SSH:
#   cat fix-tailscale-openwrt.sh | ssh root@<IP> sh -s
#
# ЖЕЛЕЗНЫЕ ПРАВИЛА:
#   ❌ Tailscale НЕ перезагружаем (оборвётся SSH)
#   ❌ Podkop НЕ рестартим (может сломать маршрутизацию)
#   ❌ firewall НЕ reload (сбросит правила Tailscale)
#   ❌ reboot НЕ делаем
# =============================================================================

# НЕ используем set -e! Каждый шаг обрабатывает ошибки сам.

# =============================================================================
# Определение версии OpenWrt
# =============================================================================
OPENWRT_VERSION=$(cat /etc/openwrt_release 2>/dev/null | grep 'DISTRIB_RELEASE' | cut -d"'" -f2)
OPENWRT_MAJOR=$(echo "$OPENWRT_VERSION" | cut -d'.' -f1)
OPENWRT_MINOR=$(echo "$OPENWRT_VERSION" | cut -d'.' -f2)

if [ -z "$OPENWRT_VERSION" ]; then
    OPENWRT_VERSION="unknown"
    OPENWRT_MAJOR="0"
    OPENWRT_MINOR="0"
fi

# Определяем тип firewall
if [ "$OPENWRT_MAJOR" -ge 25 ] 2>/dev/null; then
    FW_TYPE="fw4"
    FW_VERB="nftables"
elif [ "$OPENWRT_MAJOR" -eq 24 ] && [ "$OPENWRT_MINOR" -ge 10 ] 2>/dev/null; then
    FW_TYPE="fw4"
    FW_VERB="nftables"
else
    FW_TYPE="fw3"
    FW_VERB="iptables"
fi

# =============================================================================
# Шаг 0: Заголовок
# =============================================================================
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   УНИВЕРСАЛЬНЫЙ СПАСИТЕЛЬНЫЙ СКРИПТ             ║"
echo "║   Tailscale НЕ ТРОГАЕМ • Podkop НЕ РЕСТАРТИМ    ║"
echo "║   firewall НЕ reload • reboot НЕ ДЕЛАЕМ         ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  OpenWrt: $OPENWRT_VERSION • Firewall: $FW_TYPE ($FW_VERB)"
echo ""


# =============================================================================
# Шаг 1: Tailscale fw_mode → none
# =============================================================================
echo "━━━ [1/13] Tailscale fw_mode → none ━━━"
CURRENT_FW=""
CURRENT_FW=$(uci get tailscale.settings.fw_mode 2>/dev/null) || true
if [ "$CURRENT_FW" != "none" ]; then
    uci set tailscale.settings.fw_mode='none' 2>/dev/null || true
    uci commit tailscale 2>/dev/null || true
    echo "  ✅ fw_mode: ${CURRENT_FW:-unset} → none"
else
    echo "  ✅ fw_mode уже none"
fi

# =============================================================================
# Шаг 2: init.d/tailscale → DISABLED
# =============================================================================
echo "━━━ [2/13] init.d/tailscale → DISABLED ━━━"
if [ -f /etc/init.d/tailscale ] && /etc/init.d/tailscale enabled 2>/dev/null; then
    /etc/init.d/tailscale disable 2>/dev/null || true
    echo "  ✅ init.d/tailscale disabled"
else
    echo "  ✅ init.d/tailscale уже disabled или не найден"
fi

# =============================================================================
# Шаг 3: WAN ifname (podkop использует ifname, а не device)
# =============================================================================
echo "━━━ [3/13] WAN ifname ━━━"
WAN_IFNAME=$(uci get network.wan.ifname 2>/dev/null) || true
if [ -z "$WAN_IFNAME" ]; then
    WAN_DEVICE=$(uci get network.wan.device 2>/dev/null) || true
    if [ -n "$WAN_DEVICE" ]; then
        uci set network.wan.ifname="$WAN_DEVICE" 2>/dev/null || true
        uci commit network 2>/dev/null || true
        echo "  ✅ network.wan.ifname=$WAN_DEVICE (добавлен из device)"
    else
        echo "  ⚠️  WAN device не найден, пропускаем"
    fi
else
    echo "  ✅ network.wan.ifname=$WAN_IFNAME (уже есть)"
fi

# =============================================================================
# Шаг 4: Podkop настройки (exclude_ntp, enable_output, mixed_proxy)
# =============================================================================
echo "━━━ [4/13] Podkop настройки ━━━"

if [ -f /etc/config/podkop ]; then
    CURRENT_NTP=$(uci get podkop.settings.exclude_ntp 2>/dev/null) || true
    if [ "$CURRENT_NTP" != "1" ]; then
        uci set podkop.settings.exclude_ntp='1' 2>/dev/null || true
        echo "  ✅ exclude_ntp: ${CURRENT_NTP:-unset} → 1"
    else
        echo "  ✅ exclude_ntp уже 1"
    fi

    CURRENT_OUTPUT=$(uci get podkop.settings.enable_output_network_interface 2>/dev/null) || true
    if [ "$CURRENT_OUTPUT" != "1" ]; then
        uci set podkop.settings.enable_output_network_interface='1' 2>/dev/null || true
        echo "  ✅ enable_output_network_interface: ${CURRENT_OUTPUT:-unset} → 1"
    else
        echo "  ✅ enable_output_network_interface уже 1"
    fi

    # mixed_proxy_enabled = 0 для всех профилей
    for profile in main YT; do
        CURRENT_MIXED=$(uci get podkop.${profile}.mixed_proxy_enabled 2>/dev/null) || true
        if [ "$CURRENT_MIXED" != "0" ]; then
            uci set podkop.${profile}.mixed_proxy_enabled='0' 2>/dev/null || true
            echo "  ✅ ${profile}.mixed_proxy_enabled: ${CURRENT_MIXED:-unset} → 0"
        else
            echo "  ✅ ${profile}.mixed_proxy_enabled уже 0"
        fi
    done

    uci commit podkop 2>/dev/null || true
else
    echo "  ⚠️  /etc/config/podkop не найден, пропускаем настройки podkop"
fi

# =============================================================================
# Шаг 5: rc.local с tailscaled (userspace-networking)
# =============================================================================
echo "━━━ [5/13] rc.local ━━━"
if [ -f /etc/rc.local ] && grep -q "tailscaled" /etc/rc.local 2>/dev/null; then
    echo "  ✅ rc.local уже содержит tailscaled"
else
    # Сохраняем бэкап если есть
    [ -f /etc/rc.local ] && cp /etc/rc.local /etc/rc.local.bak 2>/dev/null || true
    
    cat > /etc/rc.local << 'EOF'
#!/bin/sh
(sleep 40
tailscaled --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 &
sleep 5
tailscale up --accept-dns=false --accept-routes
sleep 10
logger -t rc.local 'tailscale up applied') &
exit 0
EOF
    chmod +x /etc/rc.local 2>/dev/null || true
    cp /etc/rc.local /etc/rc.local.bak 2>/dev/null || true
    echo "  ✅ rc.local создан"
fi

# =============================================================================
# Шаг 6: firewall → tailscale0 в LAN зону (БЕЗ reload!)
# =============================================================================
echo "━━━ [6/13] firewall → tailscale0 в LAN зону ━━━"
echo "  ⚠️  firewall НЕ перезагружаем! (сохраняем конфиг)"
if [ -f /etc/config/firewall ]; then
    CURRENT_DEV=$(uci get firewall.@zone[0].device 2>/dev/null) || true
    if echo "$CURRENT_DEV" | grep -q "tailscale0" 2>/dev/null; then
        echo "  ✅ tailscale0 уже в LAN зоне"
    else
        uci set firewall.@zone[0].device='br-lan tailscale0' 2>/dev/null || true
        uci commit firewall 2>/dev/null || true
        echo "  ✅ tailscale0 добавлен в LAN зону (конфиг сохранён, reload НЕ делали)"
    fi
else
    echo "  ⚠️  /etc/config/firewall не найден, пропускаем"
fi

# =============================================================================
# Шаг 7: Три watchdog'а (каждые 2 минуты)
# =============================================================================
echo "━━━ [7/13] Watchdog'ы (3 шт, каждые 2 мин) ━━━"

# 7a. Tailscale watchdog — восстанавливает rc.local и tailscaled
cat > /etc/ts-watchdog.sh << 'WEOF'
#!/bin/sh
RC_BACKUP="/etc/rc.local.bak"
if [ ! -f "$RC_BACKUP" ]; then exit 1; fi
if ! grep -q "tailscaled" /etc/rc.local 2>/dev/null; then
    cp "$RC_BACKUP" /etc/rc.local 2>/dev/null || true
fi
if ! ps | grep -q "tailscaled --statedir=" 2>/dev/null; then
    (sleep 5; tailscaled --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 & sleep 5; tailscale up --accept-dns=false --accept-routes) &
fi
WEOF
chmod +x /etc/ts-watchdog.sh 2>/dev/null || true
echo "  ✅ ts-watchdog.sh"

# 7b. Podkop watchdog — перезапускает sing-box если упал
cat > /etc/podkop-watchdog.sh << 'PEOF'
#!/bin/sh
if ! ps | grep -q "sing-box run" 2>/dev/null; then
    logger -t podkop-watchdog "sing-box not running, restarting podkop"
    /etc/init.d/podkop restart 2>/dev/null || true
fi
PEOF
chmod +x /etc/podkop-watchdog.sh 2>/dev/null || true
echo "  ✅ podkop-watchdog.sh"

# 7c. Route watchdog — восстанавливает FakeIP маршруты
cat > /etc/route-watchdog.sh << 'REOF'
#!/bin/sh
if ! ip route | grep -q "198.18.0.0/15" 2>/dev/null; then
    logger -t route-watchdog "Restoring FakeIP routes"
    ip route add 198.18.0.0/15 dev br-lan 2>/dev/null || true
fi
nft list table inet PodkopTable >/dev/null 2>&1 || {
    logger -t route-watchdog "PodkopTable missing, restarting podkop"
    /etc/init.d/podkop restart 2>/dev/null || true
}
REOF
chmod +x /etc/route-watchdog.sh 2>/dev/null || true
echo "  ✅ route-watchdog.sh"

# =============================================================================
# Шаг 8: Crontab
# =============================================================================
echo "━━━ [8/13] Crontab ━━━"
(
    crontab -l 2>/dev/null | grep -v -E "(ts-watchdog|podkop-watchdog|route-watchdog|list_update)" || true
    echo "*/2 * * * * /etc/ts-watchdog.sh"
    echo "*/2 * * * * /etc/podkop-watchdog.sh"
    echo "*/2 * * * * /etc/route-watchdog.sh"
    echo "13 */3 * * * /usr/bin/podkop list_update"
) | crontab - 2>/dev/null || true
echo "  ✅ crontab обновлён (3 watchdog'а + list_update)"

# =============================================================================
# Шаг 9: check-ip скрипт диагностики
# =============================================================================
echo "━━━ [9/13] check-ip ━━━"
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
chmod +x /usr/bin/check-ip 2>/dev/null || true
echo "  ✅ /usr/bin/check-ip создан"

# =============================================================================
# Шаг 10: Установка podkop-fw4-fix (только для fw4/nftables)
# =============================================================================
echo "━━━ [10/13] podkop-fw4-fix ━━━"
if [ "$FW_TYPE" = "fw4" ]; then
    echo "  🔧 OpenWrt $OPENWRT_VERSION (fw4/nftables) — устанавливаю fw4-fix"
    wget -q -O /root/podkop-fw4-fix.sh \
      'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fw4-fix.sh' 2>/dev/null || \
    curl -sL -o /root/podkop-fw4-fix.sh \
      'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fw4-fix.sh' 2>/dev/null || \
      echo "  ⚠️  Не удалось скачать podkop-fw4-fix.sh"

    if [ -f /root/podkop-fw4-fix.sh ]; then
        chmod +x /root/podkop-fw4-fix.sh 2>/dev/null || true
        sh /root/podkop-fw4-fix.sh install 2>&1 | head -5 || true
        echo "  ✅ podkop-fw4-fix установлен"
    else
        echo "  ⚠️  podkop-fw4-fix.sh не найден, пропускаем"
    fi
else
    echo "  ⏭️  OpenWrt $OPENWRT_VERSION (fw3/iptables) — fw4-fix не требуется"
fi


# =============================================================================
# Шаг 11: Установка podkop-fix-lists
# =============================================================================
echo "━━━ [11/13] podkop-fix-lists ━━━"
wget -q -O /root/podkop-fix-lists.sh \
  'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fix-lists.sh' 2>/dev/null || \
curl -sL -o /root/podkop-fix-lists.sh \
  'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fix-lists.sh' 2>/dev/null || \
  echo "  ⚠️  Не удалось скачать podkop-fix-lists.sh"

if [ -f /root/podkop-fix-lists.sh ]; then
    chmod +x /root/podkop-fix-lists.sh 2>/dev/null || true
    sh /root/podkop-fix-lists.sh 2>&1 | head -10 || true
    echo "  ✅ podkop-fix-lists выполнен"
else
    echo "  ⚠️  podkop-fix-lists.sh не найден, пропускаем"
fi

# =============================================================================
# Шаг 12: Проверка firewall (PodkopTable жива?)
# =============================================================================
echo "━━━ [12/13] Проверка firewall ━━━"
if [ "$FW_TYPE" = "fw4" ]; then
    if nft list table inet PodkopTable >/dev/null 2>&1; then
        echo "  ✅ PodkopTable (nftables) — жива"
        nft list chain inet PodkopTable mangle 2>/dev/null | grep -c "counter packets" || true
    else
        echo "  ⚠️  PodkopTable отсутствует! Нужен /etc/init.d/podkop restart"
    fi

    if nft list chain inet fw4 mangle_forward 2>/dev/null | grep -q "podkop-fw4-fix" 2>/dev/null; then
        echo "  ✅ fw4-fix правила — есть"
    else
        echo "  ⚠️  fw4-fix правила отсутствуют"
    fi
else
    if iptables -t mangle -L PREROUTING 2>/dev/null | grep -q "Podkop" 2>/dev/null; then
        echo "  ✅ Podkop правила (iptables) — есть"
    else
        echo "  ⚠️  Podkop правила в iptables не найдены"
    fi
fi


# =============================================================================
# Шаг 13: Финальная диагностика
# =============================================================================
echo "━━━ [13/13] Финальная диагностика ━━━"

echo "--- WAN статус ---"
ubus call network.interface.wan status 2>/dev/null | grep -E '"device"|"address"|"method"' | head -5 || echo "  ⚠️  WAN не найден"

echo "--- Пинг до 1.1.1.1 ---"
ping -c 2 -W 3 1.1.1.1 2>&1 | tail -3 || true

echo "--- Пинг до google.com ---"
ping -c 2 -W 3 google.com 2>&1 | tail -3 || true

echo "--- DNS резолв ---"
nslookup google.com 1.1.1.1 2>&1 | grep -E 'Address|Name' | head -3 || echo "  ⚠️  DNS не работает"

# =============================================================================
# ФИНАЛ
# =============================================================================
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ СПАСЕНИЕ ПРИМЕНЕНО                           ║"
echo "║                                                  ║"
echo "║  Tailscale: НЕ ТРОГАЛИ (сохранён)               ║"
echo "║  Podkop: НЕ РЕСТАРТИЛИ (сохранён)               ║"
echo "║  firewall: НЕ reload (сохранён)                  ║"
echo "║  Перезагрузка: НЕ ДЕЛАЛИ                         ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Проверка:"
echo "  fw_mode:              $(uci get tailscale.settings.fw_mode 2>/dev/null || echo '?')"
echo "  exclude_ntp:          $(uci get podkop.settings.exclude_ntp 2>/dev/null || echo '?')"
echo "  enable_output_net:    $(uci get podkop.settings.enable_output_network_interface 2>/dev/null || echo '?')"
echo "  init.d/tailscale:     $([ -f /etc/init.d/tailscale ] && (/etc/init.d/tailscale enabled 2>/dev/null && echo 'ENABLED' || echo 'DISABLED') || echo 'НЕТ')"
echo "  watchdog'ов:          $(crontab -l 2>/dev/null | grep -c watchdog || echo 0) записи"
echo "  tailscaled:           $(ps 2>/dev/null | grep 'tailscaled --statedir=' | grep -v grep | head -1 | awk '{print $NF}' || echo 'НЕ ЗАПУЩЕН')"
echo "  check-ip:             $(which check-ip 2>/dev/null || echo 'НЕ НАЙДЕН')"
echo "  fw4-fix:              $(ls /root/podkop-fw4-fix.sh 2>/dev/null && echo 'OK' || echo 'НЕТ')"
echo "  fix-lists:            $(ls /root/podkop-fix-lists.sh 2>/dev/null && echo 'OK' || echo 'НЕТ')"
echo ""
echo "⏳ Автозапуск check-ip через 3 секунды..."
sleep 3
echo ""
check-ip
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ ДИАГНОСТИКА ЗАВЕРШЕНА                        ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
