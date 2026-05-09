#!/bin/bash
# Спасительный скрипт для роутера 100.70.216.65
# Применяется сразу после появления в Tailscale
# 1. Фиксит Tailscale (держит соединение)
# 2. Базовая диагностика

IP="100.70.216.65"
PASS="56756789"

echo "=== СПАСИТЕЛЬНЫЙ СКРИПТ для $IP ==="
echo ""

# 1. Проверка SSH
echo "=== 1. ПРОВЕРКА SSH ==="
sshpass -p "$PASS" ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@$IP "echo 'SSH OK'" 2>&1
if [ $? -ne 0 ]; then
  echo "❌ SSH не работает"
  exit 1
fi
echo "✅ SSH работает"

# 2. Фикс Tailscale (держатель соединения)
echo ""
echo "=== 2. ФИКС TAILSCALE ==="
sshpass -p "$PASS" ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@$IP "
echo '--- Статус tailscale ---'
tailscale status 2>/dev/null | head -5
echo ''
echo '--- Перезапуск tailscale ---'
/etc/init.d/tailscale restart 2>&1
sleep 3
echo ''
echo '--- Статус после перезапуска ---'
tailscale status 2>/dev/null | head -5
echo ''
echo '--- Добавляем watchdog в cron ---'
grep -q 'tailscale' /etc/crontabs/root 2>/dev/null || echo '*/2 * * * * /etc/init.d/tailscale restart >/dev/null 2>&1' >> /etc/crontabs/root
echo 'Cron:'
crontab -l 2>/dev/null | grep tailscale
echo ''
echo '--- Проверка uptime ---'
uptime
echo ''
echo '--- Проверка памяти ---'
free -m | head -3
" 2>&1

echo ""
echo "=== 3. БАЗОВАЯ ДИАГНОСТИКА ==="
sshpass -p "$PASS" ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@$IP "
echo '--- Модель ---'
cat /proc/cpuinfo | grep 'machine' | head -1
echo ''
echo '--- OpenWrt ---'
cat /etc/openwrt_release | grep DISTRIB_DESCRIPTION
echo ''
echo '--- WAN IP ---'
ip -4 addr show | grep 'inet ' | grep -v '127.0.0.1' | grep -v '100\.'
echo ''
echo '--- Podkop ---'
which podkop 2>/dev/null && echo 'podkop installed' || echo 'podkop NOT installed'
echo ''
echo '--- Sing-box ---'
which sing-box 2>/dev/null && echo 'sing-box installed' || echo 'sing-box NOT installed'
echo ''
echo '--- Tailscale IP ---'
tailscale ip -4 2>/dev/null
" 2>&1

echo ""
echo "=== ГОТОВО ==="
