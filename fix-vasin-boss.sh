#!/bin/bash
# fix-vasin-boss.sh — восстановление роутера Vasin Boss через AnyDesk
# Запуск: bash fix-vasin-boss.sh

echo "=== ВОССТАНОВЛЕНИЕ VASIN BOSS ==="
echo ""

# 1. fw_mode=none
echo "1. Установка fw_mode=none..."
uci set tailscale.settings.fw_mode='none'
uci commit tailscale

# 2. init.d disabled
echo "2. Отключение init.d/tailscale..."
/etc/init.d/tailscale disable

# 3. exclude_ntp=1
echo "3. Установка exclude_ntp=1..."
sed -i "s/option exclude_ntp '0'/option exclude_ntp '1'/" /etc/config/podkop
uci commit podkop

# 4. rc.local с tailscaled
echo "4. Создание rc.local с tailscaled..."
cat > /etc/rc.local << 'EOF'
#!/bin/sh
(sleep 40
tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 &
sleep 5
tailscale up --accept-dns=false --accept-routes
sleep 10
logger -t rc.local 'tailscale up applied') &
exit 0
EOF
chmod +x /etc/rc.local

# 5. Watchdog скрипт
echo "5. Создание watchdog скрипта..."
cat > /etc/ts-watchdog.sh << 'EOF'
#!/bin/sh
RC_BACKUP="/etc/rc.local.bak"
if [ ! -f "$RC_BACKUP" ]; then exit 1; fi
if ! grep -q "tailscaled" /etc/rc.local 2>/dev/null; then cp "$RC_BACKUP" /etc/rc.local; fi
if ! ps | grep -q "tailscaled --state="; then
    (sleep 5; tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 & sleep 5; tailscale up --accept-dns=false --accept-routes) &
fi
EOF
chmod +x /etc/ts-watchdog.sh

# 6. Watchdog в crontab
echo "6. Добавление watchdog в crontab..."
crontab -l 2>/dev/null | grep -v watchdog > /tmp/crontab 2>/dev/null || echo "" > /tmp/crontab
echo "*/5 * * * * /etc/ts-watchdog.sh" >> /tmp/crontab
crontab /tmp/crontab

# 7. Restart firewall
echo "7. Перезапуск firewall..."
/etc/init.d/firewall restart

# 8. Перезапуск tailscaled
echo "8. Перезапуск tailscaled..."
ps | grep "tailscaled --state=" | awk '{print $1}' | xargs kill 2>/dev/null
sleep 2
tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 &
sleep 5
tailscale up --accept-dns=false --accept-routes

# 9. Финальная проверка
echo ""
echo "=== ФИНАЛЬНАЯ ПРОВЕРКА ==="
echo "fw_mode: $(uci get tailscale.settings.fw_mode)"
echo "init.d: $(/etc/init.d/tailscale enabled && echo "ENABLED (BAD)" || echo "DISABLED (OK)")"
echo "tailscaled: $(ps | grep tailscaled | grep -v grep)"
echo "watchdog: $(crontab -l | grep watchdog)"

echo ""
echo "Ожидание 60 секунд..."
sleep 60

echo ""
echo "=== СТАТУС TAILSCALE ==="
tailscale status | head -5

echo ""
echo "=== ТЕСТЫ ==="
curl -s -o /dev/null -w "google.com: %{http_code}\n" --connect-timeout 5 "https://www.google.com"
curl -s -o /dev/null -w "youtube.com: %{http_code}\n" --connect-timeout 5 "https://www.youtube.com"

echo ""
echo "=== ГОТОВО ==="
echo "Роутер Vasin Boss восстановлен!"
