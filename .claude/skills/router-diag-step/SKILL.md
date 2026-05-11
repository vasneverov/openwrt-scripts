---
name: router-diag-step
description: Universal diagnostic step for any router. Use as FINAL step after flashing, after grooming, after any repair. Single SSH command, Karpathy-style output. Integrate into flash_router_universal.md (step 11), groom-routers (step 5), router-diagnostics, router-reboot-check.
---

# Универсальный диагностический шаг

**Goal-Driven:** 11 проверок. Каждая = 1 вопрос. Ответ = ✅ или ❌.

## Команда (один SSH)

```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@ROUTER_IP "
echo '╔══════════════════════════════════════════════╗'
echo '║  DIAG: ROUTER_NAME (ROUTER_IP)              ║'
echo '╚══════════════════════════════════════════════╝'

# 1. SYSTEM
echo ''
echo '── 1. SYSTEM ──'
echo \"Model: \$(cat /tmp/sysinfo/model 2>/dev/null)\"
echo \"OS: \$(cat /etc/openwrt_release | grep DISTRIB_RELEASE | cut -d\"'\" -f2)\"
echo \"Uptime: \$(uptime | sed 's/.*up //' | sed 's/,.*//')\"
echo \"Flash: \$(df -h / | tail -1 | awk '{print \$3\"/\"\$2}')\"

# 2. WAN
echo ''
echo '── 2. WAN ──'
echo \"GW: \$(ip route | grep default | awk '{print \$3}')\"
echo \"IF: \$(ip route | grep default | awk '{print \$5}')\"

# 3. PROVIDER (direct)
echo ''
echo '── 3. PROVIDER ──'
curl -s --connect-timeout 5 --max-time 10 https://ipinfo.io/json 2>/dev/null | grep -E '\"ip\"|\"city\"|\"org\"' | tr -d '\"' | tr ',' ' '

# 4. PROXY (via podkop)
echo ''
echo '── 4. PROXY ──'
curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -E 'ip=|loc='

# 5. TAILSCALE
echo ''
echo '── 5. TAILSCALE ──'
echo \"IP: \$(tailscale status 2>&1 | head -1 | awk '{print \$1}')\"
echo \"Status: \$(tailscale status 2>&1 | head -1 | awk '{print \$4}')\"
echo \"fw_mode: \$(uci get tailscale.settings.fw_mode)\"
echo \"init.d: \$(/etc/init.d/tailscale enabled 2>/dev/null && echo ENABLED || echo DISABLED)\"

# 6. PODKOP
echo ''
echo '── 6. PODKOP ──'
echo \"Table: \$(nft list table inet PodkopTable >/dev/null 2>&1 && echo OK || echo MISSING)\"
echo \"Lists: \$(uci get podkop.main.community_lists | wc -w) items\"
echo \"exclude_ntp: \$(uci get podkop.settings.exclude_ntp)\"

# 7. SITES (via proxy)
echo ''
echo '── 7. SITES ──'
for url in google.com youtube.com telegram.org facebook.com instagram.com rutracker.org tiktok.com x.com discord.com github.com; do
  CODE=\$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://\$url 2>/dev/null)
  printf '  %-15s %3s\n' \"\$url\" \"\$CODE\"
done

# 8. PING
echo ''
echo '── 8. PING ──'
for host in 1.1.1.1 8.8.8.8 google.com; do
  AVG=\$(ping -c 3 -W 2 \$host 2>&1 | tail -1 | grep -oE 'avg = [0-9.]+' | cut -d' ' -f3)
  echo \"  \$host: \${AVG:-❌} ms\"
done

# 9. WATCHDOG
echo ''
echo '── 9. WATCHDOG ──'
echo \"Count: \$(crontab -l | grep -c watchdog)\"

# 10. fw4-fix
echo ''
echo '── 10. fw4-fix ──'
echo \"Script: \$(ls /root/podkop-fw4-fix.sh >/dev/null 2>&1 && echo OK || echo FAIL)\"
echo \"Rules: \$(nft list chain inet fw4 mangle_forward 2>/dev/null | grep -c 'podkop-fw4-fix') active\"

# 11. rc.local
echo ''
echo '── 11. rc.local ──'
grep -q 'sleep 40' /etc/rc.local && echo 'sleep 40: YES (OLD)' || echo 'sleep 40: NO (NEW)'
grep -q tailscaled /etc/rc.local && echo 'tailscaled: OK' || echo 'tailscaled: FAIL'
grep -q 'for i in 1 2 3' /etc/rc.local && echo 'timeout: YES (NEW)' || echo 'timeout: NO (OLD)'
grep -q 'podkop-fw4-fix' /etc/rc.local && echo 'fw4-fix: OK' || echo 'fw4-fix: FAIL'
"
```

## Формат вывода

```
╔══════════════════════════════════════════════╗
║  DIAG: H-01 (100.99.69.84)                  ║
╚══════════════════════════════════════════════╝

── 1. SYSTEM ──
Model: Cudy WR3000H v1
OS: 25.12.0
Uptime: 33 min
Flash: 34.1M/44.1M

── 2. WAN ──
GW: 192.168.7.1
IF: wan

── 3. PROVIDER ──
  ip: 5.16.134.182
  city: Vidnoye
  org: AS31363 JSC ER-Telecom Holding

── 4. PROXY ──
ip=92.61.71.14
loc=CZ

── 5. TAILSCALE ──
IP: 100.99.69.84
Status: linux
fw_mode: none
init.d: DISABLED

── 6. PODKOP ──
Table: OK
Lists: 21 items
exclude_ntp: 1

── 7. SITES ──
  google.com      301
  youtube.com     301
  telegram.org    200
  facebook.com    301
  instagram.com   301
  rutracker.org   301
  tiktok.com      301
  x.com           200
  discord.com     200
  github.com      200

── 8. PING ──
  1.1.1.1: 27.1 ms
  8.8.8.8: 19.3 ms
  google.com: 19.5 ms

── 9. WATCHDOG ──
Count: 3

── 10. fw4-fix ──
Script: OK
Rules: 4 active

── 11. rc.local ──
sleep 40: NO (NEW)
tailscaled: OK
```

## Критерии успеха (Goal-Driven)

| # | Проверка | ✅ Успех | ❌ Провал |
|---|----------|---------|-----------|
| 1 | System | Модель определена, Flash > 10% | Нет модели, Flash < 10% |
| 2 | WAN | GW есть, IF есть | Нет GW |
| 3 | Provider | IP + город + провайдер | Нет ответа |
| 4 | Proxy | loc ≠ RU | loc = RU или нет |
| 5 | Tailscale | IP 100.x.x.x, fw_mode=none, init.d=DISABLED | Нет IP, fw_mode≠none, init.d=ENABLED |
| 6 | Podkop | Table OK, exclude_ntp=1, списки ≥ 20 | Table MISSING, exclude_ntp≠1 |
| 7 | Sites | Все 10 отвечают 200/301 | Любой 000 |
| 8 | Ping | Все < 50ms | Любой ❌ |
| 9 | Watchdog | ≥ 3 | < 3 |
| 10 | fw4-fix | Script OK, Rules ≥ 1 | Script FAIL |
| 11 | rc.local | sleep 40: NO, tailscaled: OK, timeout: YES, fw4-fix: OK | sleep 40: YES или tailscaled: FAIL или timeout: NO |


## Интеграция в другие скиллы

### В flash_router_universal.md (шаг 11 — финальная диагностика)

Заменить шаг 11 на:
```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ШАГ 11: Финальная диагностика"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STEP11_START=$(date +%s)

# Выполнить универсальный диагностический шаг
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@192.168.5.1 "
# ... (вставить команду из раздела "Команда (один SSH)" выше, заменив ROUTER_IP на 192.168.5.1, ROUTER_NAME на \$ROUTER_NAME)
"

STEP11_TIME=$(($(date +%s)-STEP11_START))
echo "  ⏱ $STEP11_TIME сек"

# Итоговая таблица (оставить как есть)
```

### В groom-routers/SKILL.md (шаг 5 — финальная проверка)

Заменить шаг 5 на вызов универсальной диагностики для 3-5 случайных роутеров.

### В router-diagnostics/SKILL.md

Заменить весь раздел "Формат отчёта" на ссылку на этот скилл.

### В router-reboot-check/SKILL.md

Добавить в конец: "После ребута — выполнить универсальный диагностический шаг (см. router-diag-step)."
