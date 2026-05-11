#!/bin/bash
# Rescue script applied directly on tr30_22 (100.91.90.22)
# Applied via SSH as soon as router appears

set -e

echo "=== RESCUE tr30_22 START $(date) ==="

# 1. fw_mode=none (критично для userspace tailscale)
uci set tailscale.settings.fw_mode='none'
uci commit tailscale
echo "✅ fw_mode=none"

# 2. Отключить init.d tailscale (ломает PodkopTable)
/etc/init.d/tailscale disable 2>/dev/null || true
echo "✅ init.d tailscale disabled"

# 3. Отключить autoupdate
uci set tailscale.settings.autoupdate='false'
uci commit tailscale
echo "✅ autoupdate=false"

# 4. Убедиться что tailscaled есть в rc.local
if ! grep -q tailscaled /etc/rc.local; then
    sed -i '/^exit 0/i /usr/sbin/tailscaled --state=/etc/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &' /etc/rc.local
    echo "✅ tailscaled добавлен в rc.local"
else
    # Проверить что путь к state правильный (персистентный)
    if grep -q 'tailscaled' /etc/rc.local && ! grep -q '/etc/tailscale' /etc/rc.local; then
        sed -i 's|tailscaled.*|/usr/sbin/tailscaled --state=/etc/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock \&|' /etc/rc.local
        echo "✅ tailscaled в rc.local: путь к state исправлен на /etc/tailscale"
    else
        echo "✅ tailscaled уже в rc.local"
    fi
fi

# 5. Создать директорию для state (персистентная)
mkdir -p /etc/tailscale
echo "✅ /etc/tailscale/ создана"

# 6. Скопировать state в персистентную папку если есть в /var
if [ -f /var/lib/tailscale/tailscaled.state ] && [ ! -f /etc/tailscale/tailscaled.state ]; then
    cp /var/lib/tailscale/tailscaled.state /etc/tailscale/tailscaled.state
    echo "✅ state скопирован /var/lib → /etc/tailscale"
elif [ -f /etc/tailscale/tailscaled.state ]; then
    echo "✅ state уже в /etc/tailscale"
else
    echo "⚠️  state не найден нигде — tailscale потребует повторной авторизации"
fi

# 7. exclude_ntp=1 (предотвращает DNS-петли)
uci set podkop.settings.exclude_ntp='1' 2>/dev/null && uci commit podkop 2>/dev/null && echo "✅ exclude_ntp=1" || echo "⚠️  podkop UCI не найден (ок если podkop не установлен)"

# 8. Watchdog в crontab
if ! crontab -l 2>/dev/null | grep -q watchdog; then
    (crontab -l 2>/dev/null; echo "*/5 * * * * /bin/sh /etc/tailscale-watchdog.sh") | crontab -
    echo "✅ watchdog добавлен в crontab"
else
    echo "✅ watchdog уже в crontab"
fi

# 9. Создать watchdog скрипт если нет
if [ ! -f /etc/tailscale-watchdog.sh ]; then
    cat > /etc/tailscale-watchdog.sh << 'WDOG'
#!/bin/sh
if ! tailscale status >/dev/null 2>&1; then
    logger -t tailscale-watchdog "tailscale не отвечает, перезапускаем"
    killall tailscaled 2>/dev/null; sleep 2
    /usr/sbin/tailscaled --state=/etc/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &
    sleep 5
    tailscale up --accept-routes 2>/dev/null &
fi
WDOG
    chmod +x /etc/tailscale-watchdog.sh
    echo "✅ watchdog скрипт создан"
else
    echo "✅ watchdog скрипт уже есть"
fi

echo ""
echo "=== RESCUE DONE $(date) ==="
echo ""
echo "--- Текущий статус Tailscale ---"
tailscale status 2>/dev/null | head -5 || echo "(tailscale не отвечает прямо сейчас)"
echo ""
echo "--- rc.local ---"
grep -n tailscale /etc/rc.local || echo "(не найдено)"
echo ""
echo "--- crontab ---"
crontab -l 2>/dev/null | grep -E 'watchdog|tailscale' || echo "(не найдено)"
