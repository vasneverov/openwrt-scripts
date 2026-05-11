#!/bin/sh
# rescue_tr56-13.sh — спасительный скрипт для tr56-13
# Запускать через SSH после появления роутера в Tailscale
# Цель: восстановить Tailscale, не теряя связь

set -e

echo '=== RESCUE tr56-13 ==='

# 1. Проверяем tailscaled
TS_PID=$(pidof tailscaled 2>/dev/null || echo '')
if [ -z "$TS_PID" ]; then
  echo 'tailscaled не запущен — запускаем'
  tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
  sleep 3
  tailscale up --accept-dns=false --accept-routes
  echo 'tailscaled запущен'
else
  echo "tailscaled работает (PID $TS_PID)"
fi

# 2. Проверяем tailscale0 интерфейс
if ! ip link show tailscale0 >/dev/null 2>&1; then
  echo 'tailscale0 MISSING — перезапускаем tailscaled'
  kill -9 $TS_PID 2>/dev/null || true
  sleep 2
  tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
  sleep 3
  tailscale up --accept-dns=false --accept-routes
  echo 'tailscaled перезапущен'
fi

# 3. Проверяем связь с coordination server
sleep 5
TS_STATUS=$(tailscale status 2>&1 | head -1)
echo "Tailscale статус: $TS_STATUS"

# 4. Проверяем watchdog'ы
echo ''
echo '=== Watchdog проверка ==='
for wd in ts-watchdog podkop-watchdog route-watchdog; do
  if [ -f "/etc/$wd.sh" ]; then
    echo "$wd: OK ($(ls -la /etc/$wd.sh | awk '{print $1, $NF}'))"
  else
    echo "$wd: MISSING"
  fi
done

# 5. Проверяем crontab
echo ''
echo '=== Crontab ==='
crontab -l 2>/dev/null

# 6. Проверяем rc.local
echo ''
echo '=== rc.local ==='
cat /etc/rc.local

# 7. Проверяем podkop
echo ''
echo '=== Podkop ==='
/usr/bin/podkop get_status 2>&1 || echo 'podkop status FAIL'

echo ''
echo '=== RESCUE COMPLETE ==='
echo "IP: $(tailscale status 2>&1 | head -1 | awk '{print $1}')"
echo "Status: $(tailscale status 2>&1 | head -1 | awk '{print $4}')"
