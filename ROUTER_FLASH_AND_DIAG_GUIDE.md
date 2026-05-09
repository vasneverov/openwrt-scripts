# Полное руководство: Прошивка и диагностика роутеров OpenWrt

> Документ для Claude Code. Следовать строго — каждый шаг отдельно, без объединения в скрипты.

---

## 0. ЖЕЛЕЗНЫЕ ПРАВИЛА — читать первым делом

### Правило 1 — Tailscale: наивысший приоритет

**Никогда не терять Tailscale соединение.** Это единственный канал удалённого доступа.

```
Запрещено:
❌ kill tailscaled (если это единственное соединение)
❌ /etc/init.d/tailscale restart (если fw_mode не none)
❌ tailscale serve --tcp 22 (ломает nftables, блокирует SSH)
❌ fw_mode='nftables' (только userspace режим!)
❌ reboot без 5-пунктовой проверки
```

### Правило 2 — Ребут только после явного подтверждения

Перед каждым ребутом показать пользователю:
- Причину ребута
- Результаты 5-пунктовой проверки
- Риски
- Получить явное "да"

### Правило 3 — Каждый шаг отдельно

Никогда не запускать flash-скрипт целиком. Каждый шаг — отдельный tool call с результатом.

### Правило 4 — Проверять ключи ПЕРЕД установкой в подкоп

Ключ ставится в подкоп только после `● READY ✓✓✓` от check_vless.py.

---

## 1. Определение версии роутера Cudy M3000

Единственный надёжный способ — **спросить пользователя год на серийнике**.

| Год на серийнике | Версия | Прошивка | Флаг |
|------------------|--------|----------|------|
| 24 (начало серийника 24xxxx) | v1 | `openwrt-25.12.0-...-m3000-v1-squashfs-sysupgrade.bin` | нет |
| 25 (начало серийника 25xxxx) | v2 (YT8821) | `openwrt-25.12.0-...-m3000-v1-squashfs-sysupgrade.bin` | `-F` (force) |

> **Важно:** Factory firmware v2 роутера определяет себя как "Cudy M3000 v1" — это нормально. Год серийника определяет всё.

> **Почему force для 25-го года?** Железо v2 имеет Motorcomm YT8821 PHY. Если залить v1 прошивку без --force — WAN порт не работает. Прошивка v1 + `-F` корректно работает на v2 железе и поднимает WAN.

---

## 2. Прошивка с нуля — полный workflow

### Подготовка

**Файлы прошивок (локально на Маке):**
```
~/Downloads/M3000 1.0_2.0/openwrt-25.12.0-mediatek-filogic-cudy_m3000-v1-squashfs-sysupgrade.bin
~/Downloads/M3000 1.0_2.0/backup-m3000-template.tar.gz

~/Downloads/TR3000 V1 2/openwrt-25.12.0-mediatek-filogic-cudy_tr3000-v1-squashfs-sysupgrade.bin
~/Downloads/TR3000 V1 2/backup-tr3000-template.tar.gz
```

**Сетевой адаптер Мака:** `en5` (USB LAN) — никогда не менять его настройки!

**Пароли роутеров:**
- Factory: пустой пароль
- После шаблона: `56756789`, IP `192.168.5.1`

---

### Шаг 0 — Проверка подключения и модели

```bash
ssh-keygen -R 192.168.1.1 2>/dev/null
MODEL=$(sshpass -p '' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
  -o PreferredAuthentications=password -o PubkeyAuthentication=no root@192.168.1.1 \
  "cat /tmp/sysinfo/model 2>/dev/null || cat /proc/device-tree/model" 2>/dev/null)
echo "$MODEL"
```

✅ Ожидаем: `Cudy M3000 v1` или `Cudy TR3000 v1`
❌ Пустой ответ → роутер не подключён к LAN порту

---

### Шаг 1 — Заливаем прошивку

**M3000 — только через stdin pipe (НЕ scp):**

```bash
# 24-й год (v1, без force):
FW=~/Downloads/M3000\ 1.0_2.0/openwrt-25.12.0-mediatek-filogic-cudy_m3000-v1-squashfs-sysupgrade.bin
sshpass -p '' ssh -o StrictHostKeyChecking=no root@192.168.1.1 "cat > /tmp/sysupgrade.bin" < "$FW"
sshpass -p '' ssh -o StrictHostKeyChecking=no root@192.168.1.1 "sysupgrade -n /tmp/sysupgrade.bin" || true

# 25-й год (v2/YT8821, ОБЯЗАТЕЛЬНО --force):
FW=~/Downloads/M3000\ 1.0_2.0/openwrt-25.12.0-mediatek-filogic-cudy_m3000-v1-squashfs-sysupgrade.bin
sshpass -p '' ssh -o StrictHostKeyChecking=no root@192.168.1.1 "cat > /tmp/sysupgrade.bin" < "$FW"
sshpass -p '' ssh -o StrictHostKeyChecking=no root@192.168.1.1 "sysupgrade -n -F /tmp/sysupgrade.bin" || true
```

**TR3000 — через scp:**

```bash
FW=~/Downloads/TR3000\ V1\ 2/openwrt-25.12.0-mediatek-filogic-cudy_tr3000-v1-squashfs-sysupgrade.bin
sshpass -p '' scp -O -o StrictHostKeyChecking=no root@192.168.1.1:/tmp/sysupgrade.bin "$FW"
sshpass -p '' ssh -o StrictHostKeyChecking=no root@192.168.1.1 "sysupgrade -n /tmp/sysupgrade.bin" || true
```

**Мониторинг возврата (ждать минимум 30 сек):**

```bash
START=$(date +%s)
sleep 30
while true; do
  ssh-keygen -R 192.168.1.1 2>/dev/null
  OK=$(sshpass -p '' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
    root@192.168.1.1 "grep -q '25.12' /etc/openwrt_release && echo up" 2>/dev/null)
  [ "$OK" = "up" ] && echo "✅ OpenWrt UP за $(($(date +%s)-START))s" && break
  sleep 2
done
```

---

### ⚠️ WAN проверка после flash (ТОЛЬКО для M3000 25-го года)

После заливки прошивки, **до шаблона**, проверить WAN:

```bash
sshpass -p '' ssh -o StrictHostKeyChecking=no root@192.168.1.1 "
for i in /sys/class/net/eth*; do echo \"\$(basename \$i) carrier: \$(cat \$i/carrier 2>/dev/null)\"; done
ip addr show | grep 'inet ' | grep -v 127
ip route | grep default
"
```

- `carrier: 1` на WAN интерфейсе + IP получен → ✅ продолжать
- `carrier: 0` на WAN → ❌ СТОП, перешить с правильным флагом
- `carrier: 1` но нет IP → OK, DHCP придёт позже, продолжать

---

### Шаг 2 — Шаблон + hostname

**M3000 — stdin pipe:**
```bash
RU="M56-XX"  # имя роутера
TPL=~/Downloads/M3000\ 1.0_2.0/backup-m3000-template.tar.gz

sshpass -p '' ssh -o StrictHostKeyChecking=no root@192.168.1.1 "cat > /tmp/backup.tar.gz" < "$TPL"
sshpass -p '' ssh -o StrictHostKeyChecking=no root@192.168.1.1 "
cd / && tar xzf /tmp/backup.tar.gz
uci set system.@system[0].hostname='$RU'
uci commit system
echo '$RU' > /proc/sys/kernel/hostname
uci set wireless.radio0.country='PA'
uci set wireless.radio1.country='PA'
uci commit wireless
reboot" || true
```

Шаблон устанавливает:
- IP: `192.168.5.1`, пароль: `56756789`
- LAN: br-lan, WAN: eth0 (DHCP)

**Мониторинг возврата на 192.168.5.1:**
```bash
sleep 30
while true; do
  ssh-keygen -R 192.168.5.1 2>/dev/null
  OK=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
    root@192.168.5.1 "echo up" 2>/dev/null)
  [ "$OK" = "up" ] && echo "✅ UP на 5.1" && break
  sleep 2
done
```

---

### Шаг 3 — Установка Podkop

```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
  "printf 'y\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh)"
```

Проверка:
```bash
sshpass -p '56756789' ssh root@192.168.5.1 "/usr/bin/podkop show_version 2>/dev/null"
```

---

### Шаг 4 — Конфигурация Podkop

**Стандартный город — Москва** (если пользователь не сказал другой):
- main: `bMSK:5223 → Fin4` (финский IP для заблокированных сайтов)
- YT: `bMSK:8853` (российский IP для YouTube)

**СПб вариант:**
- main: `bSPB:4191 → Fin3`
- YT: `bSPB:8853`

```bash
VLESS_MAIN='vless://UUID@HOST:PORT?...'
VLESS_YT='vless://UUID@HOST:PORT?...'

sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# Московское время
uci set system.@system[0].timezone='MSK-3'
uci set system.@system[0].zonename='Europe/Moscow'
uci commit system
/etc/init.d/sysntpd restart

# Podkop settings
uci set podkop.settings.dns_server='1.1.1.1'
uci set podkop.settings.bootstrap_dns_server='1.1.1.1'
uci set podkop.settings.dns_type='udp'
uci set podkop.settings.update_interval='3h'
uci set podkop.settings.exclude_ntp='1'
uci set podkop.settings.disable_quic='1'

# Main профиль — community lists (telegram + meta ВСЕГДА ПЕРВЫМИ!)
uci del podkop.main.community_lists 2>/dev/null || true
for l in telegram meta geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront; do
  uci add_list podkop.main.community_lists=\"\$l\"
done
uci set podkop.main.proxy_string='\${VLESS_MAIN}'
uci set podkop.main.mixed_proxy_enabled='0'
uci set podkop.main.proxy_config_type='url'

# YT профиль
uci set podkop.YT=section
uci set podkop.YT.enabled='1'
uci set podkop.YT.connection_type='proxy'
uci set podkop.YT.proxy_config_type='url'
uci del podkop.YT.community_lists 2>/dev/null || true
uci add_list podkop.YT.community_lists='youtube'
uci set podkop.YT.proxy_string='\${VLESS_YT}'
uci set podkop.YT.mixed_proxy_enabled='0'

uci commit podkop
/etc/init.d/podkop restart"

sleep 10
sshpass -p '56756789' ssh root@192.168.5.1 "ps | grep sing-box | grep -v grep && echo '✅ sing-box OK' || echo '❌ sing-box не запущен'"
```

**Критические настройки podkop:**
| Параметр | Значение | Почему |
|----------|----------|--------|
| `exclude_ntp='1'` | обязательно | NTP через FakeIP → часы дрейфуют |
| `mixed_proxy_enabled='0'` | обязательно | '1' ломает jq → sing-box не стартует |
| `proxy_config_type='url'` | обязательно | 'vless' не работает в 0.7.x |
| `dns_server='1.1.1.1'` | обязательно | оба DNS должны быть 1.1.1.1 |
| `bootstrap_dns_server='1.1.1.1'` | обязательно | оба! |
| telegram + meta — первыми | обязательно | порядок важен |

**Запрещено:**
- ❌ Профиль `calls` — удалять если обнаружен, не использовать
- ❌ Только `main` + `YT` профили

**Если sing-box не запустился (race condition):**
```bash
sleep 8 && sshpass -p '56756789' ssh root@192.168.5.1 "/etc/init.d/podkop restart"
sleep 10
sshpass -p '56756789' ssh root@192.168.5.1 "ps | grep sing-box | grep -v grep"
```

---

### Шаг 4.1 — Podkop watchdog cron

```bash
sshpass -p '56756789' ssh root@192.168.5.1 "
(crontab -l 2>/dev/null | grep -v 'podkop restart'; \
 echo '*/10 * * * * netstat -tlnp | grep -q \":1602\" || /etc/init.d/podkop restart') | crontab -
crontab -l | grep podkop"
```

---

### Шаг 5 — Tailscale установка

```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# Установка
wget -q -O /tmp/tailscale.apk 'https://gunanovo.github.io/openwrt-tailscale/aarch64_cortex-a53/tailscale-1.96.5-r1.apk'
apk add --allow-untrusted /tmp/tailscale.apk && rm -f /tmp/tailscale.apk

# Патч init.d (убрать конфликтующий --statedir)
sed -i 's|--statedir=/var/lib/tailscale ||g' /etc/init.d/tailscale

# КРИТИЧНО: init.d должен быть DISABLED
/etc/init.d/tailscale disable

# UCI настройки
rm -f /etc/nftables.d/tailscale*.nft 2>/dev/null
uci set tailscale.settings.fw_mode='none'
uci set tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
uci set tailscale.settings.autoupdate='false'
uci commit tailscale
mkdir -p /etc/tailscale

# rc.local — автозапуск после ребута
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
cp /etc/rc.local /etc/rc.local.bak

# Firewall: добавить tailscale0 в LAN зону
uci set firewall.@zone[0].device='br-lan tailscale0'
uci commit firewall
/etc/init.d/firewall reload

# Запустить tailscaled прямо сейчас
tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 &"
```

**Что должно быть в Tailscale:**
| Параметр | Значение |
|----------|----------|
| `fw_mode` | `none` |
| `init.d tailscale` | **DISABLED** |
| `tailscaled` режим | `--tun=userspace-networking` |
| `autoupdate` | `false` |
| state file | `/etc/tailscale/tailscaled.state` |
| rc.local | содержит `tailscaled --state=...` |
| rc.local.bak | существует (бэкап для watchdog) |
| tailscale0 | в firewall зоне LAN |

**Чего НЕ должно быть:**
| Запрещено | Причина |
|-----------|---------|
| `fw_mode='nftables'` | конфликт с podkop таблицами |
| `init.d tailscale ENABLED` | конфликт с нашим rc.local запуском |
| `tailscale serve --tcp 22` | блокирует SSH навсегда |
| `--state=` параметр (без dir) | ломает userspace режим |
| `autoupdate=true` | обновление может сломать конфиг |

---

### Шаг 5.2 — Podkop hotplug после tailscale0

```bash
sshpass -p '56756789' ssh root@192.168.5.1 "
mkdir -p /etc/hotplug.d/net
cat > /etc/hotplug.d/net/99-podkop-tailscale << 'HOTPLUG'
#!/bin/sh
[ \"\$ACTION\" = \"add\" ] || exit 0
[ \"\$INTERFACE\" = \"tailscale0\" ] || exit 0
(sleep 30; /etc/init.d/podkop restart) &
HOTPLUG
chmod +x /etc/hotplug.d/net/99-podkop-tailscale"
```

---

### Шаг 5.3 — Tailscale watchdog (КРИТИЧНО перед ребутом!)

```bash
sshpass -p '56756789' ssh root@192.168.5.1 "
cat > /etc/ts-watchdog.sh << 'EOF'
#!/bin/sh
RC_BACKUP=\"/etc/rc.local.bak\"
if [ ! -f \"\$RC_BACKUP\" ]; then logger -t watchdog \"rc.local.bak не найден!\"; exit 1; fi
if ! grep -q \"tailscaled\" /etc/rc.local 2>/dev/null; then
  cp \"\$RC_BACKUP\" /etc/rc.local
  logger -t watchdog \"rc.local восстановлен\"
fi
if ! ps | grep -q \"tailscaled --state=\"; then
  (sleep 5
   tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 &
   sleep 5
   tailscale up --accept-dns=false --accept-routes) &
  logger -t watchdog \"tailscaled перезапущен\"
fi
EOF
chmod +x /etc/ts-watchdog.sh
(crontab -l 2>/dev/null | grep -v ts-watchdog; echo '*/3 * * * * /etc/ts-watchdog.sh') | crontab -"
```

---

### Шаг 6 — Tailscale авторизация

```bash
# Запустить tailscale up
sshpass -p '56756789' ssh root@192.168.5.1 \
  "setsid tailscale up --accept-dns=false --accept-routes --reset > /tmp/tsup.log 2>&1 &"

# Получить URL (поллить каждые 2 сек)
for i in $(seq 1 20); do
  URL=$(sshpass -p '56756789' ssh root@192.168.5.1 \
    "grep -o 'https://login.tailscale.com[^ ]*' /tmp/tsup.log 2>/dev/null" | head -1)
  [ -n "$URL" ] && echo "🔗 $URL" && break
  sleep 2
done
```

Мониторить авторизацию самому (не спрашивать "готово"):
```bash
for i in $(seq 1 60); do
  sleep 3
  STATUS=$(sshpass -p '56756789' ssh -o ConnectTimeout=3 root@192.168.5.1 \
    "tailscale status 2>&1 | head -1" 2>/dev/null)
  echo "$STATUS" | grep -q "100\." && echo "✅ Авторизован: $STATUS" && break
done
```

После авторизации — сброс serve конфига:
```bash
sshpass -p '56756789' ssh root@192.168.5.1 "tailscale serve reset 2>&1; tailscale serve status 2>&1"
# Ожидаем: "No serve config"
```

---

### Шаг 7 — 5-пунктовая проверка ПЕРЕД ребутом

```bash
sshpass -p '56756789' ssh root@192.168.5.1 "
echo '1. init.d:' && /etc/init.d/tailscale enabled && echo '❌ ENABLED' || echo '✅ DISABLED'
echo '2. fw_mode:' && uci get tailscale.settings.fw_mode
echo '3. rc.local:' && grep -q tailscaled /etc/rc.local && echo '✅ OK' || echo '❌ FAIL'
echo '4. watchdog:' && crontab -l | grep ts-watchdog || echo '❌ НЕТ'
echo '5. exclude_ntp:' && uci get podkop.settings.exclude_ntp
echo '6. Tailscale IP:' && tailscale status | head -1"
```

**Все должны быть OK:**
- init.d: `DISABLED` ✅
- fw_mode: `none` ✅
- rc.local: `OK` ✅
- watchdog: строка crontab ✅
- exclude_ntp: `1` ✅

**Хотя бы один FAIL → не ребутить, сначала починить!**

---

### Шаг 8 — Ребут и мониторинг

```bash
sshpass -p '56756789' ssh root@192.168.5.1 "reboot" || true
echo "🔄 Ребут отправлен в $(date '+%H:%M:%S')"
START=$(date +%s)
sleep 80  # МИНИМУМ 80 секунд!
while true; do
  ssh-keygen -R 192.168.5.1 2>/dev/null
  STATUS=$(sshpass -p '56756789' ssh -o ConnectTimeout=3 root@192.168.5.1 \
    "tailscale status 2>&1 | head -1" 2>/dev/null)
  echo "$STATUS" | grep -q "100\." && echo "✅ Tailscale UP за $(($(date +%s)-START))с" && break
  echo "⏳ $(($(date +%s)-START))с..."
  sleep 3
done
```

---

### Шаг 8.1 — Финальная проверка после ребута

```bash
sshpass -p '56756789' ssh root@192.168.5.1 "
hostname
grep DISTRIB_RELEASE /etc/openwrt_release
ps | grep -E 'tailscaled|sing-box|crond' | grep -v grep
uci get tailscale.settings.fw_mode
/etc/init.d/tailscale enabled && echo '❌ init.d ENABLED' || echo '✅ init.d DISABLED'
tailscale status | head -1
wc -c < /etc/tailscale/tailscaled.state
curl -s -o /dev/null -w 'Google: %{http_code}\n' --connect-timeout 5 https://www.google.com
curl -s -o /dev/null -w 'YouTube: %{http_code}\n' --connect-timeout 5 https://www.youtube.com"
```

**Ожидаемые результаты:**
- tailscaled: запущен с `--tun=userspace-networking` ✅
- sing-box: запущен ✅
- fw_mode: `none` ✅
- init.d: `DISABLED` ✅
- State: >2000 байт ✅
- Google: `200` ✅
- YouTube: `200` ✅

---

## 3. Создание VLESS ключей

### Серверная топология

| Город | Main (зарубежный IP) | YT (российский IP) |
|-------|----------------------|--------------------|
| Москва | `bMSK:5223 → Fin4` | `bMSK:8853` |
| СПб | `bSPB:4191 → Fin3` | `bSPB:8853` |

### Параметры серверов

**bSPB relay (5.35.84.151) — порты:**
| Порт | Назначение | pbk | sid |
|------|------------|-----|-----|
| 4191 | → Fin3 (главный, СПб) | `XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw` | `932e706c` |
| 8853 | YT direct (bSPB) | `me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM` | `ddcb53b3` |
| 2090 | → Italy | `OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI` | `c30f9fec74087d32` |

**bMSK relay (159.194.198.172) — порты:**
| Порт | Назначение | pbk | sid |
|------|------------|-----|-----|
| 5223 | → Fin4 (главный, Москва) | (уточнить из панели bMSK) | — |
| 8853 | YT direct (bMSK) | (уточнить из панели bMSK) | — |

### Формат VLESS URL

```
vless://UUID@HOST:PORT?type=grpc&security=reality&mode=gun&serviceName=&pbk=PBK&sid=SID&sni=www.apple.com&fp=chrome&spx=%2F#LABEL
```

**Обязательно:**
- `type=grpc` (НЕ tcp)
- `fp=chrome`
- `sni=www.apple.com`
- Нет `/` перед `?`

### Добавление клиента на Fin3 (main, СПб)

Панель: `https://144.31.66.115:5050/5050/`, логин `ad` / пароль `56`

```bash
# Генерация UUID
UUID=$(python3 -c "import uuid; print(uuid.uuid4())")

# Добавить клиента через API
ONE_YEAR_MS=$(python3 -c "import time; print(int((time.time()+365*24*3600)*1000))")
ROUTER_NAME="M56-XX"

curl -sk -X POST "https://144.31.66.115:5050/5050/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"ad","password":"56"}' -c /tmp/fin3.txt > /dev/null

curl -sk -b /tmp/fin3.txt -X POST "https://144.31.66.115:5050/5050/panel/api/inbounds/addClient" \
  -H "Content-Type: application/json" \
  -d "{\"id\":3,\"settings\":\"{\\\"clients\\\":[{\\\"id\\\":\\\"$UUID\\\",\\\"email\\\":\\\"${ROUTER_NAME}_Fin3\\\",\\\"limitIp\\\":0,\\\"enable\\\":true,\\\"expiryTime\\\":$ONE_YEAR_MS,\\\"totalGB\\\":1099511627776}]}\"}"

rm -f /tmp/fin3.txt
```

### После добавления клиента — проверить xray

```bash
sshpass -p 'Ujkjdf56' ssh root@144.31.66.115 \
  "grep -c '$UUID' /usr/local/x-ui/bin/config.json"
# Если 0 → kill -9 $(pgrep xray) → xray перезапустится → снова grep → должно быть >0
```

### Проверка ключей (ОБЯЗАТЕЛЬНО перед подкопом)

```bash
echo 'vless://...' | python3 ~/CLAUDECODE/check_vless.py -
```

**Требуемый результат:**
```
● TCP   ● TLS   ● xray   ● expiry   ● limit
● READY ✓✓✓  всё проверено, ключ рабочий
```

**Если xray FAIL:** `kill -9 $(pgrep xray)` на сервере → подождать 3 сек → снова проверить.

**Ключ ставится в подкоп ТОЛЬКО после READY!**

---

## 4. Диагностика удалённых роутеров

### Обязательная 8-компонентная диагностика

```bash
IP="100.x.x.x"  # Tailscale IP роутера
PASS="56756789"

sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$IP "
echo '=== 1. СИСТЕМА ==='
hostname && grep DISTRIB_RELEASE /etc/openwrt_release

echo '=== 2. TAILSCALE ==='
tailscale status 2>&1 | head -3
ps | grep 'tailscaled --state=' | grep -v grep || echo '❌ tailscaled НЕ запущен'
uci get tailscale.settings.fw_mode 2>/dev/null
/etc/init.d/tailscale enabled && echo '❌ init.d ENABLED' || echo '✅ init.d DISABLED'
grep -q tailscaled /etc/rc.local 2>/dev/null && echo '✅ rc.local OK' || echo '❌ rc.local FAIL'
crontab -l 2>/dev/null | grep ts-watchdog && echo '✅ watchdog OK' || echo '❌ watchdog НЕТ'

echo '=== 3. PODKOP ==='
ps | grep sing-box | grep -v grep || echo '❌ sing-box не запущен'
uci get podkop.settings.exclude_ntp 2>/dev/null
uci get podkop.settings.dns_server 2>/dev/null
crontab -l | grep podkop || echo '❌ podkop watchdog нет'

echo '=== 4. СЕТЬ ==='
for i in /sys/class/net/eth*; do echo \"\$(basename \$i) carrier: \$(cat \$i/carrier 2>/dev/null)\"; done
ip route | grep default

echo '=== 5. КЛЮЧИ (main) ==='
uci get podkop.main.proxy_string 2>/dev/null | head -c 80

echo '=== 6. ТЕСТЫ ==='
curl -s -o /dev/null -w 'Google: %{http_code}\n' --connect-timeout 5 https://www.google.com
curl -s -o /dev/null -w 'YouTube: %{http_code}\n' --connect-timeout 5 https://www.youtube.com

echo '=== 7. ДИСКОВОЕ МЕСТО ==='
df -h | grep -E 'overlay|/dev/'

echo '=== 8. ЛОГИ ОШИБОК ==='
logread 2>/dev/null | grep -iE 'error|fail|watchdog' | tail -5
"
```

---

### Типичные проблемы и решения

#### Проблема: Telegram/Meta не работают

**Причина:** Неправильные community_lists или неверный relay адрес.

```bash
# Проверить community_lists
sshpass -p '56756789' ssh root@$IP "uci show podkop.main.community_lists"
# telegram и meta должны быть ПЕРВЫМИ

# Проверить relay адрес
sshpass -p '56756789' ssh root@$IP "uci get podkop.main.proxy_string" | head -c 50
# Для СПб: должно быть 5.35.84.151:4191
# Для Москвы: должно быть relay bMSK адрес
```

#### Проблема: YouTube не работает

```bash
# Проверить YT профиль
sshpass -p '56756789' ssh root@$IP "
uci show podkop.YT
uci get podkop.YT.proxy_string | head -c 60"
# YT должен использовать прямой bSPB:8853 или bMSK:8853
```

#### Проблема: sing-box не запускается

```bash
# Race condition — перезапустить с ожиданием
sshpass -p '56756789' ssh root@$IP "/etc/init.d/podkop restart"
sleep 8
sshpass -p '56756789' ssh root@$IP "ps | grep sing-box | grep -v grep"

# Если overlay full (нет места)
sshpass -p '56756789' ssh root@$IP "df -h | grep overlay"
# Если <5% свободно → удалить .unverified файлы:
# sshpass -p '56756789' ssh root@$IP "rm -f /root/.cache/tailscale-update/*.unverified"
```

#### Проблема: Tailscale серая точка / не онлайн

Признаки:
- `tailscale status` пустой или `Tailscale is stopped`
- Точка в мониторинге серая несколько минут

```bash
# 1. Проверить процесс
sshpass -p '56756789' ssh root@$IP "ps | grep tailscaled | grep -v grep"

# 2. Если нет — проверить rc.local
sshpass -p '56756789' ssh root@$IP "cat /etc/rc.local | grep tailscaled"

# 3. Если rc.local повреждён — восстановить
sshpass -p '56756789' ssh root@$IP "cp /etc/rc.local.bak /etc/rc.local"

# 4. Запустить вручную
sshpass -p '56756789' ssh root@$IP "
tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 &
sleep 5
tailscale up --accept-dns=false --accept-routes"
```

**Если роутер потерян (нет ни Tailscale, ни LAN доступа):**
1. Попросить пользователя зайти через AnyDesk
2. Открыть терминал в AnyDesk
3. Выполнить команды восстановления выше

#### Проблема: tailscale status показывает "-" вместо "online"

Это критично для S78 роутеров — симптом неправильного `exclude_ntp`.

```bash
sshpass -p '56756789' ssh root@$IP "uci get podkop.settings.exclude_ntp"
# Должно быть 1
# Если нет:
sshpass -p '56756789' ssh root@$IP "
uci set podkop.settings.exclude_ntp='1'
uci commit podkop"
```

#### Проблема: fw_mode не 'none'

```bash
sshpass -p '56756789' ssh root@$IP "
uci set tailscale.settings.fw_mode='none'
uci commit tailscale"
# После этого потребуется ребут — сначала проверить 5 пунктов!
```

#### Проблема: init.d tailscale ENABLED

```bash
sshpass -p '56756789' ssh root@$IP "/etc/init.d/tailscale disable"
# Потом проверить что tailscaled запущен нашим способом (userspace)
```

#### Проблема: профиль 'calls' в podkop

```bash
# Найти
sshpass -p '56756789' ssh root@$IP "cat /etc/config/podkop | grep -i calls"
# Удалить
sshpass -p '56756789' ssh root@$IP "uci delete podkop.calls 2>/dev/null; uci commit podkop"
```

---

### Диагностика до ребута (7 пунктов)

Всегда проверять перед любым ребутом удалённого роутера:

```bash
sshpass -p '56756789' ssh root@$IP "
echo '1.' && /etc/init.d/tailscale enabled && echo 'FAIL:ENABLED' || echo 'OK:DISABLED'
echo '2.' && uci get tailscale.settings.fw_mode
echo '3.' && grep -q tailscaled /etc/rc.local && echo 'OK:rc.local' || echo 'FAIL:rc.local'
echo '4.' && crontab -l | grep ts-watchdog && echo '(watchdog OK)' || echo 'FAIL:watchdog'
echo '5.' && uci get podkop.settings.exclude_ntp
echo '6.' && ls /etc/rc.local.bak 2>/dev/null && echo 'OK:bak' || echo 'FAIL:bak'
echo '7.' && tailscale status | head -1"
```

**Если хоть один FAIL → не ребутить, починить сначала.**

---

### Тайминги ребута (ориентиры)

| Модель | LAN UP | Tailscale UP |
|--------|--------|--------------|
| Cudy TR3000 v1 | ~20-30с | ~60-80с |
| Cudy M3000 v1/v2 | ~20-30с | ~60-85с |
| Xiaomi AX3000T | ~25-35с | ~70-90с |

**Никогда не проверять Tailscale раньше 80 секунд после ребута.**

---

## 5. Справочник аккаунтов Tailscale

| Учётка | Назначение | Используется для |
|--------|------------|------------------|
| `n78rout` | Основная для новых роутеров | M56-xx, TR56-07+, Z56-121+ |
| `ne78va` | Московская серия | M78-xx |
| `56papezde` | СПб серия | z56-xx (старые) |
| `vas.neverov` | Личная | S78, WBR, сервисные |

---

## 6. Контрольный список финальной проверки

После любой прошивки или ремонта обязательно проверить:

- [ ] Google.com → 200
- [ ] YouTube.com → 200
- [ ] Telegram (через DNS fakeIP или тест с телефона)
- [ ] Tailscale IP присвоен и онлайн
- [ ] fw_mode = none
- [ ] init.d tailscale = DISABLED
- [ ] rc.local содержит tailscaled
- [ ] watchdog в crontab (*/3)
- [ ] exclude_ntp = 1
- [ ] sing-box запущен
- [ ] State file > 2000 байт
- [ ] Ребут прошёл успешно (Tailscale поднялся)

---

*Документ составлен по реальному опыту прошивки 25+ роутеров. Все правила — из реальных инцидентов.*

---

## 7. Все модели роутеров — сводная таблица

| Серия | Модель | Прошивка | SCP метод | Шаблон | Пакетный менеджер | Tailscale |
|-------|--------|----------|-----------|--------|-------------------|-----------|
| z56-xxx | Cudy WR3000H v1 | `openwrt-25.12.0-...-wr3000h-v1-sysupgrade.bin` | scp -O | есть | apk | gunanovo APK |
| TR56-xxx | Cudy TR3000 v1 | `openwrt-25.12.0-...-tr3000-v1-sysupgrade.bin` | scp -O | есть | apk | gunanovo APK |
| M56-xxx | Cudy M3000 v1 (24год) | `openwrt-25.12.0-...-m3000-v1-sysupgrade.bin` | **stdin pipe** | есть | apk | gunanovo APK |
| M56-xxx / M78-xxx | Cudy M3000 v2 (25год, YT8821) | то же + **`-F`** | **stdin pipe** | есть | apk | gunanovo APK |
| S78-xxx | Cudy WR3000S v1 | `openwrt-25.12.0-...-wr3000s-v1-sysupgrade.bin` | scp -O | есть | apk / opkg | gunanovo APK |
| — | Xiaomi AX3000T | `openwrt-25.12.2-...-ax3000t-sysupgrade.bin` | scp -O | **нет шаблона** | apk | `apk add tailscale` |

**Factory IP:** всегда `192.168.1.1`, пароль пустой  
**После шаблона:** `192.168.5.1`, пароль `56756789`  
**AX3000T после flash:** `192.168.1.1`, пароль пустой, IP менять вручную через UCI

---

## 8. Xiaomi AX3000T — полный паттерн

### Главные отличия от Cudy

| Параметр | Cudy роутеры | AX3000T |
|----------|-------------|---------|
| Шаблон .tar.gz | ✅ есть | ❌ нет — всё руками |
| Tailscale пакет | gunanovo APK | `apk add tailscale` |
| init.d tailscale | DISABLED | **DISABLED** (тоже!) |
| Tailscale режим | userspace-networking | **userspace-networking** (тоже!) |
| WiFi включение | одна команда | **два уровня** — radio + VAP |
| LAN netmask | из шаблона | **вручную 255.255.255.0 обязательно!** |

### Прошивка AX3000T — Шаг 1

Роутер может быть на любом IP (старый OpenWrt).

```bash
FW=~/Downloads/AX3000T/openwrt-25.12.2-mediatek-filogic-xiaomi_mi-router-ax3000t-squashfs-sysupgrade.bin
OLD_IP="192.168.X.1"  # старый IP роутера
PASS="56756789"       # пароль если уже был OpenWrt, или пустой если factory

sshpass -p "$PASS" scp -O -o StrictHostKeyChecking=no "$FW" root@$OLD_IP:/tmp/sysupgrade.bin
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$OLD_IP "sysupgrade -n /tmp/sysupgrade.bin" || true
```

Мониторинг возврата на 192.168.1.1:
```bash
sleep 45
while true; do
  ssh-keygen -R 192.168.1.1 2>/dev/null
  OK=$(sshpass -p '' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
    root@192.168.1.1 "grep -q '25.12' /etc/openwrt_release && echo up" 2>/dev/null)
  [ "$OK" = "up" ] && echo "✅ AX3000T UP" && break
  sleep 2
done
```

### Прошивка AX3000T — Шаг 2: базовая настройка (на 192.168.1.1)

```bash
NAME="имя-роутера"

sshpass -p '' ssh -o StrictHostKeyChecking=no root@192.168.1.1 "
# Пароль
printf '%s\n%s\n' '56756789' '56756789' | passwd root

# Hostname и время
uci set system.@system[0].hostname='$NAME'
uci set system.@system[0].timezone='MSK-3'
uci set system.@system[0].zonename='Europe/Moscow'
uci commit system

# LAN IP — ОБЯЗАТЕЛЬНО с netmask!
uci set network.lan.ipaddr='192.168.5.1'
uci set network.lan.netmask='255.255.255.0'
uci commit network

# WiFi — ОБА уровня (radio + VAP)!
uci set wireless.radio0.disabled='0'
uci set wireless.radio1.disabled='0'
uci set wireless.default_radio0.disabled='0'
uci set wireless.default_radio1.disabled='0'
uci set wireless.radio0.country='PA'
uci set wireless.radio1.country='PA'
uci set wireless.default_radio0.ssid='@skynet'
uci set wireless.default_radio0.encryption='psk2'
uci set wireless.default_radio0.key='56756789'
uci set wireless.default_radio1.ssid='@skynet'
uci set wireless.default_radio1.encryption='psk2'
uci set wireless.default_radio1.key='56756789'
uci commit wireless

/etc/init.d/network reload"
```

Далее подключаться на `192.168.5.1` с паролем `56756789`.

### Tailscale на AX3000T (отличается от Cudy!)

```bash
# НЕ gunanovo APK — стандартный пакет OpenWrt
apk add tailscale

# Всё остальное — ИДЕНТИЧНО Cudy:
/etc/init.d/tailscale disable
uci set tailscale.settings.fw_mode='none'
uci set tailscale.settings.autoupdate='false'
uci commit tailscale
mkdir -p /etc/tailscale

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
cp /etc/rc.local /etc/rc.local.bak

# Watchdog
cat > /etc/ts-watchdog.sh << 'WD'
#!/bin/sh
RC_BACKUP="/etc/rc.local.bak"
if [ ! -f "$RC_BACKUP" ]; then exit 1; fi
if ! grep -q "tailscaled" /etc/rc.local 2>/dev/null; then cp "$RC_BACKUP" /etc/rc.local; fi
if ! ps | grep -q "tailscaled --state="; then
  (sleep 5; tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 & sleep 5; tailscale up --accept-dns=false --accept-routes) &
fi
WD
chmod +x /etc/ts-watchdog.sh
(crontab -l 2>/dev/null | grep -v ts-watchdog; echo '*/3 * * * * /etc/ts-watchdog.sh') | crontab -

# Запустить сейчас
tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 &
```

> **Почему userspace на AX3000T?** OpenWrt 25.12 не имеет `iptables` в PATH. Kernel-mode tailscaled ищет iptables при старте и падает в crash loop. Userspace-networking не зависит от iptables вообще.

### Ключи для AX3000T (город Москва по умолчанию)

- Main: UUID на Fin4 → relay через bMSK `159.194.198.172:5223 → Fin4`
- YT: UUID на bMSK → direct `159.194.198.172:8853`

Панели:
- Fin4: `https://45.155.55.198:5050/5050/`, логин `ad` / пароль `56`
- bMSK: `https://159.194.198.172:5050/5050/`, логин `ad` / пароль `56`

После добавления клиента — проверить grep UUID в config.json и kill -9 xray если нужно.

### Диагностика AX3000T — особые проверки

```bash
IP="100.x.x.x"

sshpass -p '56756789' ssh root@$IP "
echo '=== AX3000T специфика ==='

echo 'netmask LAN:'
uci get network.lan.netmask  # должно быть 255.255.255.0, не 255.255.255.255

echo 'WiFi VAP статус:'
uci get wireless.default_radio0.disabled 2>/dev/null  # должно быть 0
uci get wireless.default_radio1.disabled 2>/dev/null  # должно быть 0

echo 'tailscaled команда (userspace?):'
ps | grep 'tailscaled --state=' | grep -v grep

echo 'Tailscale пакет (не gunanovo):'
apk list 2>/dev/null | grep tailscale || echo 'apk list недоступен'
"
```

**Частая проблема AX3000T — нет DHCP:**  
Причина: `netmask='255.255.255.255'` (/32) вместо `/24`. Исправление:
```bash
sshpass -p '56756789' ssh root@$IP "
uci set network.lan.netmask='255.255.255.0'
uci commit network
/etc/init.d/network reload"
```

---

## 9. Cudy WR3000H (серия z56) — особенности

**Прошивка:** `~/Downloads/WR3000H/openwrt-25.12.0-mediatek-filogic-cudy_wr3000h-v1-squashfs-sysupgrade.bin`  
**Шаблон:** `~/Downloads/WR3000H/backup-wr3000h-template.tar.gz`  
**SCP метод:** обычный `scp -O` (не stdin pipe)

```bash
FW=~/Downloads/WR3000H/openwrt-25.12.0-mediatek-filogic-cudy_wr3000h-v1-squashfs-sysupgrade.bin
sshpass -p '' scp -O -o StrictHostKeyChecking=no "$FW" root@192.168.1.1:/tmp/sysupgrade.bin
sshpass -p '' ssh -o StrictHostKeyChecking=no root@192.168.1.1 "sysupgrade -n /tmp/sysupgrade.bin" || true
```

Шаблон и всё остальное — идентично Cudy TR3000/M3000 (кроме stdin pipe).

**Ключи WR3000H (СПб серия):**
- main: relay bSPB:4191 → Fin3
- YT: direct bSPB:8853

---

## 10. Cudy WR3000S (серия S78) — особенности

**Прошивка:** `~/Downloads/WR3000S V1/openwrt-25.12.0-mediatek-filogic-cudy_wr3000s-v1-squashfs-sysupgrade.bin`  
**Шаблон:** `~/Downloads/WR3000S V1/backup-wr3000s-template.tar.gz`  
**SCP метод:** обычный `scp -O`

### Критический нюанс: exclude_ntp зависит от версии podkop

| Версия podkop | Где exclude_ntp |
|---------------|-----------------|
| 25.12.x (podkop 0.7.x) | `podkop.settings.exclude_ntp` |
| 24.10.x (podkop старый) | `podkop.main.exclude_ntp` |

**Диагностика:**
```bash
# Проверить где реально лежит exclude_ntp
sshpass -p '56756789' ssh root@$IP "
uci get podkop.settings.exclude_ntp 2>/dev/null && echo 'в settings' || \
uci get podkop.main.exclude_ntp 2>/dev/null && echo 'в main' || \
echo 'НЕТ — критично, надо поставить!'
"
```

**Симптом проблемы:** `tailscale status` показывает `-` вместо `online` (не офлайн, а прочерк). Причина — часы дрейфуют из-за NTP через FakeIP.

**Исправление для старого podkop:**
```bash
sshpass -p '56756789' ssh root@$IP "
uci set podkop.main.exclude_ntp='1'
uci commit podkop
/etc/init.d/podkop restart"
```

### Пакетный менеджер на S78

S78 роутеры могут работать на OpenWrt 24.10.x:
- `apk` → OpenWrt 25.12.x
- `opkg` → OpenWrt 24.10.x

**Проверка версии:**
```bash
sshpass -p '56756789' ssh root@$IP "grep DISTRIB_RELEASE /etc/openwrt_release"
```

**Установка tailscale на 24.10.x:**
```bash
opkg update && opkg install tailscale
```

---

## 11. Cudy TR3000 v1 (серия TR56) — особенности

**Прошивка:** `~/Downloads/TR3000 V1 2/openwrt-25.12.0-mediatek-filogic-cudy_tr3000-v1-squashfs-sysupgrade.bin`  
**Шаблон:** `~/Downloads/TR3000 V1 2/backup-tr3000-template.tar.gz`  
**SCP метод:** обычный `scp -O`

**Ключи TR56 (СПб серия):**
- TR56-01..06: main через Fin3 relay, YT через bSPB:8853
- TR56-07+: main через Italy relay (bSPB:2090 → Italy), YT через bSPB:8853

```bash
# Italy relay URL:
# vless://UUID@5.35.84.151:2090?type=grpc&security=reality&...pbk=OBa4...&sid=c30f9fec74087d32&sni=www.apple.com&fp=chrome#LABEL
```

---

## 12. Ремонт удалённого роутера — общий алгоритм

### Принцип: не чинить симптом, чинить всё

Ремонтный роутер может иметь сразу несколько проблем. Всегда проходить полный чек-лист, не останавливаться после первого исправления.

### Шаг 1: полная диагностика (раздел 4)

Запустить 8-компонентную диагностику, записать все FAIL.

### Шаг 2: исправление в правильном порядке

1. Сначала сеть и WAN (без интернета ничто не установится)
2. Потом podkop (sing-box, ключи, community lists)
3. Потом Tailscale resilience (rc.local, watchdog, fw_mode, init.d)
4. В конце — ребут с 5-пунктовой проверкой

### Шаг 3: финальный тест

```bash
IP="100.x.x.x"
sshpass -p '56756789' ssh root@$IP "
curl -s -o /dev/null -w 'Google: %{http_code}\n' --connect-timeout 5 https://www.google.com
curl -s -o /dev/null -w 'YouTube: %{http_code}\n' --connect-timeout 5 https://www.youtube.com"
# Google → 200 ✅
# YouTube → 200 ✅
```

Дополнительно проверить с телефона:
- Telegram (несколько минут после ребута — подтягиваются community lists)
- Meta (Instagram/WhatsApp)

### Если нет доступа по Tailscale

Порядок попыток восстановления:
1. Попросить пользователя зайти на `192.168.5.1` по LAN и проверить LuCI
2. Попросить пользователя открыть AnyDesk → терминал → команды восстановления
3. В AnyDesk выполнить:

```bash
# Восстановление tailscaled одной командой:
mkdir -p /etc/tailscale && \
tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 & \
sleep 8 && \
tailscale up --accept-dns=false --accept-routes --reset
# Скопировать URL из вывода и открыть в браузере
```

4. Если AnyDesk недоступен → физический ребут роутера пользователем → watchdog поднимет Tailscale

---

## 13. Добавление новых ключей к существующему роутеру

Когда ключ истёк или нужно заменить:

```bash
IP="100.x.x.x"

# 1. Создать новый UUID и добавить клиента на сервер (см. раздел 3)
# 2. Проверить через check_vless.py → READY ✓✓✓
# 3. Применить на роутере:
sshpass -p '56756789' ssh root@$IP "
uci set podkop.main.proxy_string='vless://НОВЫЙ_КЛЮЧ'
uci commit podkop
/etc/init.d/podkop restart"
sleep 10
sshpass -p '56756789' ssh root@$IP "ps | grep sing-box | grep -v grep && echo OK"

# 4. Старый UUID удалить с панели X-UI
```

**Никогда не удалять старый UUID до того, как новый ключ проверен и установлен.**
