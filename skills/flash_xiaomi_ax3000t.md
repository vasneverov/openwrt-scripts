# Скилл: Прошивка Xiaomi AX3000T (AX334T) на OpenWrt 25.12

> **Модель:** Xiaomi Mi Router AX3000T (он же AX334T)  
> **Архитектура:** mediatek-filogic  
> **OpenWrt:** 25.12.2  
> **Пакетный менеджер:** apk (НЕ opkg!)  
> **Эталон:** 19-ternovsky (100.88.218.14) — уже прошит на 24.10.1  
> **Схема:** 1 профиль main (через relay) — YouTube 3-м списком после telegram, meta

---

## 1. Подготовка

### 1.1 Файлы

| Файл | Путь |
|------|------|
| **Прошивка 25.12.2** | `~/Downloads/AX3000T/openwrt-25.12.2-mediatek-filogic-xiaomi_mi-router-ax3000t-squashfs-sysupgrade.bin` |
| **Backup-шаблон** | Нужно создать (см. шаг 3) |
| **Ключ main** | Создать через скилл `create_clone_key.md` (см. раздел 3) |

### 1.2 Подключение

Роутер подключается **кабелем** к Mac. После прошивки:
- **192.168.1.1** — без пароля (стоковый OpenWrt)
- **192.168.5.1** — после применения шаблона (пароль `56756789`)

### 1.3 Особенности Xiaomi AX3000T

- **НЕ Cudy M3000** — прошивка другая (`xiaomi_mi-router-ax3000t`, не `cudy_m3000`)
- **Нет v1/v2 разделения** — одна прошивка для всех ревизий
- **initramfs не нужен** — sysupgrade с загрузчика (через SSH)
- **Первый вход** — через SSH на 192.168.1.1 (без пароля)

### 1.4 ⚠️ ВАЖНО: Смена LAN IP на OpenWrt 25.12 (apk)

На OpenWrt 25.12 (apk-based) **синтаксис настройки LAN IP отличается** от старых версий!

**Старый синтаксис (OpenWrt 23.05 / 24.10 — opkg):**
```bash
uci set network.lan.ipaddr='192.168.5.1'
uci set network.lan.netmask='255.255.255.0'
```

**Новый синтаксис (OpenWrt 25.12 — apk):**
```bash
uci del network.lan.ipaddr 2>/dev/null
uci del network.lan.netmask 2>/dev/null
uci add_list network.lan.ipaddr='192.168.5.1/24'
```

**Почему так:** В 25.12 IP и маска задаются одной строкой через `list ipaddr` (а не через отдельные `option ipaddr` + `option netmask`). Маска указывается в CIDR-нотации прямо в IP-адресе.

**Как выглядит в /etc/config/network (правильно):**
```
config interface 'lan'
    option device 'br-lan'
    option proto 'static'
    list ipaddr '192.168.5.1/24'    # ← IP + маска в одной строке через list
    option ip6assign '60'
```

**Как НЕ надо (старый формат — сломает сеть на 25.12):**
```
config interface 'lan'
    option device 'br-lan'
    option proto 'static'
    option ipaddr '192.168.5.1'      # ← НЕПРАВИЛЬНО для 25.12!
    option netmask '255.255.255.0'   # ← НЕПРАВИЛЬНО для 25.12!
```

**Проверка после смены:**
```bash
uci show network.lan.ipaddr
# Должно быть: network.lan.ipaddr=192.168.5.1/24
# НЕ ДОЛЖНО быть: network.lan.ipaddr='192.168.5.1' (без маски)
```

### 1.5 🔍 ВАЖНО: Проверка WAN после каждой операции

После **каждой значимой операции** (прошивка, применение шаблона, установка podkop, настройка podkop, ребут) — **обязательно проверять интернет на WAN порту**.

**Зачем:** Чтобы сразу отловить проблемы с подключением к провайдеру, а не гадать потом, почему podkop не работает.

**Команда проверки WAN:**
```bash
# Проверить что WAN получил IP от провайдера
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@<ROUTER_IP> "
echo '=== WAN STATUS ==='
ubus call network.interface.wan status 2>/dev/null | grep -E '\"device\"|\"address\"|\"method\"' | head -5
echo ''
echo '=== ПИНГ ДО ДНС ==='
ping -c 2 -W 3 1.1.1.1 2>&1 | tail -3
echo ''
echo '=== ПИНГ ДО GOOGLE ==='
ping -c 2 -W 3 google.com 2>&1 | tail -3
echo ''
echo '=== DNS РЕЗОЛВ ==='
nslookup google.com 1.1.1.1 2>&1 | grep -E 'Address|Name' | head -3
"
```

**Критерии успеха:**
- ✅ WAN получил IP (address вида `100.x.x.x` или `10.x.x.x` или публичный)
- ✅ Пинг до 1.1.1.1 проходит (0% packet loss)
- ✅ Пинг до google.com проходит (резолвится домен)
- ✅ DNS работает (nslookup возвращает IP)

**Если WAN не работает — СТОП.** Дальше идти нельзя, пока не починить WAN:
1. Проверить кабель (WAN порт, а не LAN!)
2. `ubus call network.interface.wan status` — есть ли IP?
3. `dmesg | grep eth` — видит ли интерфейс?
4. `swconfig dev switch0 show` — статус портов (если есть swconfig)

---

## 2. Алгоритм прошивки (12 шагов)


### Шаг 0: Проверка роутера

```bash
# Подключиться кабелем к LAN порту
# Убедиться что IP 192.168.1.1 доступен
ping -c 2 192.168.1.1

# Проверить модель
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "cat /tmp/sysinfo/model"
# Должно быть: Xiaomi Mi Router AX3000T

# Проверить текущую прошивку (если уже OpenWrt)
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "cat /etc/openwrt_release"
```

### Шаг 1: Заливка OpenWrt 25.12.2

```bash
# Скопировать прошивку
scp -O -o StrictHostKeyChecking=no \
  ~/Downloads/AX3000T/openwrt-25.12.2-mediatek-filogic-xiaomi_mi-router-ax3000t-squashfs-sysupgrade.bin \
  root@192.168.1.1:/tmp/firmware.bin

# Прошить
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "sysupgrade -n /tmp/firmware.bin"

# Ждать перезагрузки (2-3 минуты)
sleep 120

# Проверить что поднялся
ssh-keygen -R 192.168.1.1 2>/dev/null
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "cat /etc/openwrt_release | grep RELEASE"
# Должно быть: 25.12.2

# 🔍 ПРОВЕРКА WAN ПОСЛЕ ПРОШИВКИ
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "
echo '=== WAN STATUS ==='
ubus call network.interface.wan status 2>/dev/null | grep -E '\"device\"|\"address\"|\"method\"' | head -5
echo ''
echo '=== ПИНГ ДО ДНС ==='
ping -c 2 -W 3 1.1.1.1 2>&1 | tail -3
echo ''
echo '=== ПИНГ ДО GOOGLE ==='
ping -c 2 -W 3 google.com 2>&1 | tail -3
"
# ❌ Если WAN не работает — СТОП! Проверить кабель в WAN порту!
```

### Шаг 2: Создание backup-шаблона


**Если шаблона нет** — создать на свежепрошитом роутере:

```bash
# Настроить базовые параметры
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "
uci set system.@system[0].hostname='AX3000T-TEMPLATE'
uci set system.@system[0].timezone='MSK-3'
uci set system.@system[0].zonename='Europe/Moscow'
uci set wireless.radio0.country='PA'
uci set wireless.radio1.country='PA'
uci commit

# Сменить пароль
passwd root  # пароль: 56756789

# Создать backup
sysupgrade -b /tmp/backup-ax3000t-template.tar.gz
"

# Скачать шаблон на Mac
scp -O -o StrictHostKeyChecking=no \
  root@192.168.1.1:/tmp/backup-ax3000t-template.tar.gz \
  ~/Downloads/AX3000T/backup-ax3000t-template.tar.gz
```

### Шаг 3: Применить шаблон + hostname

```bash
# Скопировать шаблон
scp -O -o StrictHostKeyChecking=no \
  ~/Downloads/AX3000T/backup-ax3000t-template.tar.gz \
  root@192.168.1.1:/tmp/backup.tar.gz

# Применить
ssh -o StrictHostKeyChecking=no root@192.168.1.1 "
cd / && tar xzf /tmp/backup.tar.gz
uci set system.@system[0].hostname='<ROUTER_NAME>'
uci commit system
echo '<ROUTER_NAME>' > /proc/sys/kernel/hostname
reboot
"

# ⏱ ЖИВОЙ МОНИТОРИНГ: ждём пока роутер перезагрузится на 192.168.5.1
# Вместо sleep 60 — проверяем ping каждые 2 секунды
echo "⏳ Ожидание перезагрузки на 192.168.5.1..."
WAIT_START=$(date +%s)
while true; do
  if ping -c 1 -W 1 192.168.5.1 >/dev/null 2>&1; then
    echo "  ✅ Роутер поднялся на 192.168.5.1 через $(($(date +%s)-WAIT_START)) сек"
    break
  fi
  # Таймаут 90 секунд на всякий случай
  if [ $(($(date +%s)-WAIT_START)) -gt 90 ]; then
    echo "  ❌ Таймаут! Роутер не поднялся за 90 сек"
    exit 1
  fi
  sleep 2
done

ssh-keygen -R 192.168.5.1 2>/dev/null
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "echo OK"

# 🔍 ПРОВЕРКА WAN ПОСЛЕ ПРИМЕНЕНИЯ ШАБЛОНА
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
echo '=== WAN STATUS ==='
ubus call network.interface.wan status 2>/dev/null | grep -E '\"device\"|\"address\"|\"method\"' | head -5
echo ''
echo '=== ПИНГ ДО ДНС ==='
ping -c 2 -W 3 1.1.1.1 2>&1 | tail -3
echo ''
echo '=== ПИНГ ДО GOOGLE ==='
ping -c 2 -W 3 google.com 2>&1 | tail -3
"
# ❌ Если WAN не работает — СТОП! Шаблон мог сломать network config!
```

### Шаг 4: Создать ключ main (через relay)


> **Вызвать скилл `skills/create_clone_key.md`**

Ключ создаётся на relay-сервере (русский сервер, который DNATит на целевой).  
Для AX3000T используется схема: **bSPB:8448 → CZ2:8448** (как на 19-ternovsky).

```bash
# 4a. Проверить текущий ключ на эталонном роутере (если есть)
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@100.88.218.14 \
  "uci get podkop.main.proxy_string"

# 4b. Создать новый ключ через create_vless_key.py
python3 /Users/vas/CLAUDECODE/tools/create_vless_key.py \
  --router <ROUTER_NAME> \
  --panel-ip 92.61.71.14 \
  --panel-port 5050 \
  --inbound-id 18 \
  --relay-ip 5.35.84.151 \
  --relay-port 8448 \
  --pbk "FyCxYT4Ku_RyR7r2dZYofYxcAOm5xJtgP-T_xjgVnCQ" \
  --sid "dcaa"

# 4c. Проверить ключ
python3 /Users/vas/CLAUDECODE/check_vless.py "vless://<NEW_UUID>@..."
# Должен быть: TCP OK + TLS OK → READY
```

**Альтернатива — Fin4 через bMSK relay (для московской схемы):**
```bash
python3 /Users/vas/CLAUDECODE/tools/create_vless_key.py \
  --router <ROUTER_NAME> \
  --panel-ip 45.155.55.198 \
  --panel-port 5050 \
  --inbound-id 1 \
  --relay-ip 159.194.198.172 \
  --relay-port 5223 \
  --pbk "HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI" \
  --sid "4b929012"
```

### Шаг 5: Установка Podkop (с толстым sing-box)

> **Важно:** Для Xiaomi AX3000T (128MB flash) устанавливаем **толстый sing-box** (`sing-box`, не `sing-box-tiny`).  
> Для роутеров с малым объёмом flash (Cudy M3000, WR3000H/S) — **тонкий** `sing-box-tiny` (UPX-сжатый).

```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# Установка podkop из репозитория itdoginfo
# Скрипт сам тянет sing-box из репозитория itdoginfo (толстый, не UPX)
# Ответы на вопросы: 'y' на всё, язык интерфейса — русский (ru)
printf 'y\ny\nru\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh)
"

# 🔍 ПРОВЕРКА WAN ПОСЛЕ УСТАНОВКИ PODKOP
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
echo '=== WAN STATUS ==='
ubus call network.interface.wan status 2>/dev/null | grep -E '\"device\"|\"address\"|\"method\"' | head -5
echo ''
echo '=== ПИНГ ДО ДНС ==='
ping -c 2 -W 3 1.1.1.1 2>&1 | tail -3
echo ''
echo '=== ПИНГ ДО GOOGLE ==='
ping -c 2 -W 3 google.com 2>&1 | tail -3
"
# ❌ Если WAN не работает — podkop мог сломать сеть!
```

### Шаг 6: Настройка Podkop (один профиль main)


```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# Timezone
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
uci set podkop.settings.download_lists_via_proxy='0'
uci set podkop.settings.download_community_lists_via_proxy='0'
uci set podkop.settings.enable_output_network_interface='1'

# Community lists — ВАЖНЫЙ ПОРЯДОК: telegram, meta, youtube, потом остальные
uci del podkop.main.community_lists 2>/dev/null || true
uci add_list podkop.main.community_lists='telegram'
uci add_list podkop.main.community_lists='meta'
uci add_list podkop.main.community_lists='youtube'
for l in geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront; do
  uci add_list podkop.main.community_lists=\"\$l\"
done

# Main proxy — один ключ на всё (через relay)
uci set podkop.main.proxy_string='<VLESS_MAIN_KEY>'
uci set podkop.main.proxy_config_type='url'
uci set podkop.main.mixed_proxy_enabled='0'

# YT профиль НЕ СОЗДАЁМ — YouTube идёт через main

uci commit podkop
/etc/init.d/podkop restart
"

# 🔍 ПРОВЕРКА WAN ПОСЛЕ НАСТРОЙКИ PODKOP
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
echo '=== WAN STATUS ==='
ubus call network.interface.wan status 2>/dev/null | grep -E '\"device\"|\"address\"|\"method\"' | head -5
echo ''
echo '=== ПИНГ ДО ДНС ==='
ping -c 2 -W 3 1.1.1.1 2>&1 | tail -3
echo ''
echo '=== ПИНГ ДО GOOGLE ==='
ping -c 2 -W 3 google.com 2>&1 | tail -3
"
# ❌ Если WAN не работает — podkop restart мог сломать маршрутизацию!
```

### Шаг 7: Установка Tailscale (из репозитория gunano)

> **Важно:** Tailscale устанавливаем из репозитория **gunano** (gunanovo.github.io/openwrt-tailscale).  
> Репозиторий сам определяет архитектуру роутера через `opkg print-architecture` и автоматически выбирает нужную версию:  
> - Для Xiaomi AX3000T (128MB flash) — **толстый** `tailscale` (полная версия)  
> - Для Cudy M3000, WR3000H/S (мало flash) — **UPX-сжатый** `tailscale` (тонкая версия)  
>
> **Важно:** После установки **обязательно отключаем автообновление** Tailscale (`autoupdate=false`),  
> потому что автообновление на OpenWrt 25.12 не работает и только создаёт мусор в логах.

```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# ===== Установка Tailscale из репозитория gunano =====
# gunano — сторонний репозиторий с собранными пакетами для OpenWrt
# tailscale от gunano работает стабильнее на OpenWrt 25.12
# Репозиторий сам определяет архитектуру и выбирает толстую/UPX версию

# Очистить дублирующиеся записи (если были)
grep -v 'openwrt-tailscale' /etc/opkg/customfeeds.conf > /tmp/feeds.tmp 2>/dev/null
mv /tmp/feeds.tmp /etc/opkg/customfeeds.conf 2>/dev/null

# Добавить ключ репозитория
wget -O /tmp/key-build.pub https://gunanovo.github.io/openwrt-tailscale/key-build.pub 2>/dev/null
opkg-key add /tmp/key-build.pub 2>/dev/null
rm /tmp/key-build.pub 2>/dev/null

# Добавить репозиторий с автоопределением архитектуры
echo \"src/gz openwrt-tailscale https://gunanovo.github.io/openwrt-tailscale/\$(opkg print-architecture | awk 'NF==3 && \\\$3~/^[0-9]+\$/ {print \\\$2}' | tail -1)\" >> /etc/opkg/customfeeds.conf

# Обновить и установить
opkg update
opkg install tailscale

# Фикс для OpenWrt 25.12
sed -i 's|--statedir=/var/lib/tailscale ||g' /etc/init.d/tailscale
sed -i 's|TS_DEBUG_FIREWALL_MODE=\"none\"|TS_DEBUG_FIREWALL_MODE=\"\$fw_mode\"|g' /etc/init.d/tailscale

# Настройка
uci set tailscale.settings.fw_mode='none'
uci set tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
uci set tailscale.settings.autoupdate='false'  # ← ОБЯЗАТЕЛЬНО! Автообновление не работает на 25.12
uci commit tailscale
mkdir -p /etc/tailscale

# Отключаем init.d (будет через rc.local)
/etc/init.d/tailscale disable
"
```

### Шаг 8: Спасительные скрипты + watchdog + fw4-fix + check-ip

```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
# ===== 8a. rc.local =====
cat > /etc/rc.local << 'EOF'
#!/bin/sh
(sleep 40
tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
sleep 5
tailscale up --accept-dns=false --accept-routes
sleep 10
logger -t rc.local 'tailscale up applied') &
exit 0
EOF
chmod +x /etc/rc.local
cp /etc/rc.local /etc/rc.local.bak

# ===== 8b. Firewall — tailscale0 в LAN =====
uci set firewall.@zone[0].device='br-lan tailscale0'
uci commit firewall
/etc/init.d/firewall reload

# ===== 8c. WAN ifname (podkop использует ifname, а не device) =====
WAN_IFNAME=\$(uci get network.wan.ifname 2>/dev/null)
if [ -z \"\$WAN_IFNAME\" ]; then
    WAN_DEVICE=\$(uci get network.wan.device 2>/dev/null)
    if [ -n \"\$WAN_DEVICE\" ]; then
        uci set network.wan.ifname=\"\$WAN_DEVICE\"
        uci commit network
    fi
fi

# ===== 8d. Tailscale watchdog =====
cat > /etc/ts-watchdog.sh << 'WEOF'
#!/bin/sh
RC_BACKUP='/etc/rc.local.bak'
[ -f \"\$RC_BACKUP\" ] || exit 1
grep -q 'tailscaled' /etc/rc.local 2>/dev/null || cp \"\$RC_BACKUP\" /etc/rc.local
ps | grep -q 'tailscaled --statedir=' || {
  logger -t ts-watchdog 'tailscaled не найден, перезапуск'
  (sleep 5; tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
   sleep 5; tailscale up --accept-dns=false --accept-routes) &
}
WEOF
chmod +x /etc/ts-watchdog.sh

# ===== 8e. Podkop watchdog =====
cat > /etc/podkop-watchdog.sh << 'PEOF'
#!/bin/sh
if ! ps | grep -q 'sing-box run'; then
    logger -t podkop-watchdog 'sing-box not running, restarting podkop'
    /etc/init.d/podkop restart
fi
PEOF
chmod +x /etc/podkop-watchdog.sh

# ===== 8f. Route watchdog =====
cat > /etc/route-watchdog.sh << 'REOF'
#!/bin/sh
nft list table inet PodkopTable >/dev/null 2>&1 || {
    logger -t route-watchdog 'PodkopTable missing, restarting podkop'
    /etc/init.d/podkop restart
}
REOF
chmod +x /etc/route-watchdog.sh

# ===== 8g. Crontab =====
(crontab -l 2>/dev/null | grep -v -E '(ts-watchdog|podkop-watchdog|route-watchdog|list_update)'
 echo '*/2 * * * * /etc/ts-watchdog.sh'
 echo '*/2 * * * * /etc/podkop-watchdog.sh'
 echo '*/2 * * * * /etc/route-watchdog.sh'
 echo '13 */3 * * * /usr/bin/podkop list_update'
) | crontab -

# ===== 8h. check-ip скрипт =====
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
  CODE=\$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://\$url 2>/dev/null)
  TIME=\$(curl -s -o /dev/null -w '%{time_total}' --max-time 8 https://\$url 2>/dev/null)
  printf '%-15s %3s  (%ss)\n' \"\$url\" \"\$CODE\" \"\$TIME\"
done
CIPEOF
chmod +x /usr/bin/check-ip

# ===== 8i. Установка podkop-fw4-fix =====
# Скачать с GitHub
wget -q -O /root/podkop-fw4-fix.sh \
  'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fw4-fix.sh' 2>/dev/null
chmod +x /root/podkop-fw4-fix.sh 2>/dev/null
/root/podkop-fw4-fix.sh install 2>/dev/null || true

# ===== 8j. Установка podkop-fix-lists =====
wget -q -O /root/podkop-fix-lists.sh \
  'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fix-lists.sh' 2>/dev/null
chmod +x /root/podkop-fix-lists.sh 2>/dev/null
sh /root/podkop-fix-lists.sh 2>/dev/null || true
"

# 🔍 ПРОВЕРКА WAN ПОСЛЕ СПАСИТЕЛЬНЫХ СКРИПТОВ
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
echo '=== WAN STATUS ==='
ubus call network.interface.wan status 2>/dev/null | grep -E '\"device\"|\"address\"|\"method\"' | head -5
echo ''
echo '=== ПИНГ ДО ДНС ==='
ping -c 2 -W 3 1.1.1.1 2>&1 | tail -3
echo ''
echo '=== ПИНГ ДО GOOGLE ==='
ping -c 2 -W 3 google.com 2>&1 | tail -3
"
# ❌ Если WAN не работает — firewall reload или WAN ifname могли сломать сеть!
```

### Шаг 9: Запуск Tailscale + авторизация


```bash
# ⚠️ ВАЖНО: Перед запуском tailscaled убедиться что podkop уже работает и даёт прокси!
# Проверить что прокси работает:
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -E 'ip=|loc='
"
# Должен быть loc= не RU (например CZ, PL, DE)

# Запустить tailscaled
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
"
sleep 3

# Получить ссылку авторизации
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
setsid tailscale up --accept-dns=false --accept-routes --reset > /tmp/tsup.log 2>&1 &
"
sleep 6

TS_URL=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
  "grep -o 'https://login.tailscale.com[^ ]*' /tmp/tsup.log 2>/dev/null" | head -1)

echo "🔗 АВТОРИЗУЙ В TAILSCALE (учётка n78rout@gmail.com):"
echo "   $TS_URL"
open "$TS_URL" 2>/dev/null || true

# Ждать авторизации — мониторить статус каждые 3 секунды
echo "⏳ Ожидание авторизации Tailscale..."
AUTH_START=$(date +%s)
while true; do
  TS_STATUS=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 \
    "tailscale status 2>&1 | head -1" 2>/dev/null)
  echo "  [$(($(date +%s)-AUTH_START))c] $TS_STATUS"
  echo "$TS_STATUS" | grep -q "100\." && break
  sleep 3
done

TS_IP=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 \
  "tailscale status 2>&1 | head -1" | awk '{print $1}')
echo "✅ Tailscale авторизован: $TS_IP (за $(($(date +%s)-AUTH_START)) сек)"

# ⚠️ ВАЖНО: Сразу после авторизации проверить что Tailscale ONLINE
# (прочерк в статусе вместо "offline")
echo "⏳ Ожидание зелёной точки (Tailscale ONLINE)..."
ONLINE_START=$(date +%s)
while true; do
  TS_STATUS=$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 \
    "tailscale status 2>&1 | head -1" 2>/dev/null)
  # Прочерк в 4-м поле = ONLINE
  STATUS_FIELD=$(echo "$TS_STATUS" | awk '{print $4}')
  echo "  [$(($(date +%s)-ONLINE_START))c] $TS_STATUS"
  [ "$STATUS_FIELD" = "-" ] && break
  sleep 3
done
echo "✅ Tailscale ONLINE (зелёная точка) — за $(($(date +%s)-ONLINE_START)) сек"

# Проверить ping до роутера по Tailscale
ping -c 2 -W 3 $TS_IP 2>&1 | tail -3
```

### Шаг 10: Проверка перед ребутом (5 пунктов)

```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "
echo 'fw_mode:      ' \$(uci get tailscale.settings.fw_mode)
echo 'init.d:       ' \$(/etc/init.d/tailscale enabled 2>/dev/null && echo ENABLED || echo DISABLED)
echo 'rc.local:     ' \$(grep -q tailscaled /etc/rc.local && echo OK || echo FAIL)
echo 'watchdog:     ' \$(crontab -l | grep -c watchdog)
echo 'exclude_ntp:  ' \$(uci get podkop.settings.exclude_ntp)
echo 'fw4-fix:      ' \$(ls /root/podkop-fw4-fix.sh 2>/dev/null && echo OK || echo FAIL)
echo 'check-ip:     ' \$(which check-ip 2>/dev/null || echo FAIL)
"
```

### Шаг 11: Ребут + мониторинг

```bash
# ⏱ ЗАСЕЧЬ ВРЕМЯ
echo "🕐 РЕБУТ: \$(date +%H:%M:%S)"
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "reboot"

# ⏱ МОНИТОРИНГ ПОСЛЕ РЕБУТА (в фоне)
# Ждать 30 сек пока роутер загрузится
sleep 30

# Мониторить каждые 5-10 секунд
REBOOT_START=$(date +%s)
TS_ONLINE=false
PROXY_ONLINE=false

for i in \$(seq 1 30); do
  NOW=\$(date +%H:%M:%S)
  ELAPSED=\$((\$(date +%s)-REBOOT_START))
  
  # Проверить прокси
  PROXY=\$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 \
    "curl -s --connect-timeout 3 --max-time 5 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -E 'ip=|loc='" 2>/dev/null)
  
  # Проверить Tailscale
  TS_STATUS=\$(sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 \
    "tailscale status 2>&1 | head -1" 2>/dev/null)
  
  # Проверить ping по Tailscale
  TS_PING=\$(ping -c 1 -W 2 100.98.211.40 2>/dev/null | grep -o 'time=.*' | cut -d= -f2)
  
  echo "[\$NOW] +\${ELAPSED}s | Proxy: \${PROXY:-N/A} | TS: \${TS_STATUS:-N/A} | Ping: \${TS_PING:-N/A}"
  
  # Отметить когда прокси поднялся
  if [ "\$PROXY_ONLINE" = false ] && echo "\$PROXY" | grep -q 'loc='; then
    echo "  ✅ Прокси поднялся на +\${ELAPSED}s секунде!"
    PROXY_ONLINE=true
  fi
  
  # Отметить когда Tailscale поднялся
  if [ "\$TS_ONLINE" = false ] && echo "\$TS_STATUS" | grep -q "100\."; then
    echo "  ✅ Tailscale поднялся на +\${ELAPSED}s секунде!"
    TS_ONLINE=true
  fi
  
  # Если всё зелёное — можно выходить раньше
  if [ "\$PROXY_ONLINE" = true ] && [ "\$TS_ONLINE" = true ] && [ -n "\$TS_PING" ]; then
    echo "  ✅ ВСЁ РАБОТАЕТ! Выход из мониторинга."
    break
  fi
  
  sleep 5
done

# Финальная проверка после ребута
echo ""
echo "=== ФИНАЛЬНАЯ ПРОВЕРКА ПОСЛЕ РЕБУТА ==="
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.5.1 "
echo '--- Время работы ---'
uptime
echo ''
echo '--- Podkop ---'
echo \"Ключ: \$(uci get podkop.main.proxy_string | cut -c1-40)...\"
echo \"PodkopTable: \$(nft list table inet PodkopTable >/dev/null 2>&1 && echo OK || echo MISSING)\"
echo ''
echo '--- Tailscale ---'
tailscale status 2>&1 | head -3
echo ''
echo '--- Прокси ---'
curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -E 'ip=|loc='
echo ''
echo '--- Сайты ---'
for url in google.com youtube.com telegram.org github.com; do
  CODE=\$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://\$url 2>/dev/null)
  echo \"  \$url: \$CODE\"
done
echo ''
echo '--- Watchdog ---'
crontab -l | grep -c watchdog
echo ''
echo '--- fw4-fix ---'
/root/podkop-fw4-fix.sh update 2>&1 | tail -2
"
echo ""
echo "✅ РЕБУТ ЗАВЕРШЁН: +\$((\$(date +%s)-REBOOT_START)) секунд"
```

### Шаг 12: Финальная диагностика (check-ip)


```bash
# Проверка с роутера
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@192.168.5.1 "check-ip"

# Критерии успеха:
# ✅ cloudflare.com/cdn-cgi/trace → loc= не RU (страна НЕ Россия)
# ✅ ident.me → IP не российский
# ✅ youtube.com → 200
# ✅ telegram.org → 200
# ✅ google.com → 200
# ✅ ipinfo.io → loc=RU (этот сайт не в списках podkop — нормально)

# Если check-ip показывает Россию — проверить:
# 1. nft list chain inet PodkopTable mangle — счётчики > 0?
# 2. nft list chain inet fw4 mangle_forward — есть podkop-fw4-fix правила?
# 3. /root/podkop-fw4-fix.sh update
# 4. /etc/init.d/podkop restart
```

---

## 3. Создание ключа main (вызов скилла create_clone_key)

> **Подробный алгоритм:** `skills/create_clone_key.md`

### Кратко:

1. **Определить relay-сервер** (по городу):
   - СПб → bSPB:4191 → Fin3 (pbk=`XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw`, sid=`932e706c`)
   - Москва → bMSK:5223 → Fin4 (pbk=`HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI`, sid=`4b929012`)
   - CZ2 (универсальный) → bSPB:8448 → CZ2 (pbk=`FyCxYT4Ku_RyR7r2dZYofYxcAOm5xJtgP-T_xjgVnCQ`, sid=`dcaa`)

2. **Создать клиента** через `create_vless_key.py` (НЕ через curl к API!)

3. **Проверить ключ** через `check_vless.py` — должен быть READY

4. **Установить на роутер** — `uci set podkop.main.proxy_string='...'` + `uci commit`

---

## 4. Rescue-скрипт (если роутер уже прошит)

Если роутер уже на OpenWrt и нужно применить спасительный скрипт:

```bash
cat ~/CLAUDECODE/rescue_generic.sh | \
  sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@<TAILSCALE_IP> sh -s
```

---

## 5. Важные отличия от Cudy M3000

| Параметр | Cudy M3000 | Xiaomi AX3000T |
|----------|-----------|----------------|
| Прошивка | `cudy_m3000-v1` или `v2-yt8821` | `xiaomi_mi-router-ax3000t` |
| Backup-шаблон | `backup-m3000-template.tar.gz` | `backup-ax3000t-template.tar.gz` |
| v1/v2 | Есть (по серийнику) | Нет разделения |
| Первый вход | 192.168.1.1 без пароля | 192.168.1.1 без пароля |
| После шаблона | 192.168.5.1 (пароль 56756789) | 192.168.5.1 (пароль 56756789) |
| Эталон | M56-13 | 19-ternovsky (100.88.218.14) |

---

## 6. Железные правила (для всех прошивок)

1. **Один профиль main** — YT профиль НЕ создаём. YouTube = 3-й список (после telegram, meta)
2. **Ключ всегда через relay** — русский relay-сервер, НЕ direct
3. **Ключи создавать только через `create_vless_key.py`** — НЕ через curl к API
4. **Перед установкой ключ проверить** `check_vless.py` → READY
5. **После замены ключа podkop НЕ перезагружать** — только `uci commit`
6. **Всегда ставить 3 watchdog'а** — ts-watchdog, podkop-watchdog, route-watchdog
7. **Всегда ставить fw4-fix** — иначе forwarded трафик не маркируется
8. **Всегда ставить check-ip** — для быстрой диагностики
9. **Перед ребутом проверять 5 пунктов** — fw_mode, init.d, rc.local, watchdog, exclude_ntp
10. **Финальная диагностика** — `check-ip` с роутера (loc=не RU)

---

## 7. Уроки с 19-ternovsky (Xiaomi AX3000T)

1. **Podkop status = not running** — это нормально для OpenWrt 25.12
2. **download_lists_via_proxy=0** — иначе sing-box падает при загрузке списков
3. **raw.githubusercontent.com блокируется** — нужен podkop-fix-lists.sh
4. **fw4-fix обязателен** — иначе forwarded трафик (с клиентов) не маркируется
5. **fakeIP (198.18.0.0/15)** — это нормально, так работает podkop/sing-box
6. **Проверять сайты с `-L`** (follow redirects) — иначе 301/302 будут ошибкой
7. **enable_output_network_interface=1** — чтобы трафик с самого роутера тоже шёл через прокси

---

## 8. 🆕 Уроки с x54-yarmoshuk (ребут Tailscale + OpenWrt 25.12)

> **Дата:** 2026-05-08  
> **Роутер:** x54-yarmoshuk (Xiaomi AX3000T, OpenWrt 25.12)  
> **Проблема:** Tailscale не поднимался после ребута — серая точка, crash loop  
> **Решение:** fix-tailscale-openwrt.sh + ручной перезапуск tailscaled с правильными параметрами

### 8.1 Хронология ребута (подтверждено замерами)

```
22:58:27  🔴 reboot отправлен
22:59:12  Роутер загрузился (+45с)
22:59:21  ✅ Podkop поднялся — прокси через PL (+54с)
22:59:30  ✅ Прокси переключился на CZ2 (+63с)
22:59:46  Tailscale — Health check (+79с)
22:59:52  ✅ Tailscale ONLINE (+85с)
23:00:15  ✅ Ping по Tailscale 3.4ms (+108с)
```

**Итого:** 1 мин 25 сек до полной готовности.

### 8.2 Почему Tailscale не поднимался (корень проблемы)

1. **init.d/tailscale** запускал tailscaled **без** `--tun=userspace-networking` и с `fw_mode=nftables`
2. На OpenWrt 25.12 **нет iptables** — tailscaled падал с ошибкой
3. **procd** видел что tailscaled упал и перезапускал его снова — **crash loop**
4. Точка была **серая** (offline)

### 8.3 Что исправили

| Проблема | Исправление |
|----------|-------------|
| init.d запускал без `--tun=userspace-networking` | **init.d DISABLED** — tailscaled через rc.local |
| fw_mode=nftables (нет iptables) | **fw_mode=none** |
| crash loop от procd | **rc.local** запускает через 40 сек после загрузки |
| Нет интернета для Tailscale при старте | **Podkop стартует первым** (30 сек) — даёт прокси через CZ2 |

### 8.4 Ключевые изменения в алгоритме прошивки

**Что было неправильно (старый скилл):**
1. ❌ **Не проверял что прокси работает** перед запуском tailscaled
2. ❌ **Не ждал зелёную точку** после авторизации — сразу шёл к ребуту
3. ❌ **Не мониторил ребут** — просто `sleep 90` и проверка
4. ❌ **Не проверял 5 пунктов** перед ребутом (добавлено позже)
5. ❌ **Не было проверки что Tailscale ONLINE** после авторизации

**Что исправлено (новый скилл):**
1. ✅ **Шаг 9: проверка прокси** перед запуском tailscaled — `curl cloudflare.com/cdn-cgi/trace`
2. ✅ **Шаг 9: ожидание зелёной точки** — цикл до `STATUS_FIELD = "-"`
3. ✅ **Шаг 11: мониторинг ребута** с посекундным логом (Proxy, TS, Ping)
4. ✅ **Шаг 10: проверка 5 пунктов** перед ребутом
5. ✅ **Шаг 9: ping по Tailscale** после авторизации

### 8.5 Последовательность после ребута (гарантированная)

```
0-30 сек:  Загрузка OpenWrt
30-40 сек: Podkop стартует → интернет через CZ2 есть
40-45 сек: rc.local запускает tailscaled с --tun=userspace-networking
45-60 сек: tailscaled подключается к controlplane через CZ2 → зелёная точка
```

**Почему это работает:**
- Podkop (sing-box) не зависит от Tailscale — стартует на старте системы
- Когда через 40 сек стартует tailscaled — у него уже есть рабочий интернет через CZ2
- `fw_mode=none` — tailscaled не лезет в firewall
- `--tun=userspace-networking` — не требует iptables/nftables
- 3 watchdog'а страхуют каждые 2 минуты

### 8.6 Что делать если Tailscale не зеленеет после ребута

```bash
# 1. Проверить что прокси работает
ssh root@192.168.5.1 "curl -s https://cloudflare.com/cdn-cgi/trace | grep -E 'ip=|loc='"

# 2. Проверить что tailscaled запущен
ssh root@192.168.5.1 "ps | grep tailscaled | grep -v grep"

# 3. Проверить fw_mode
ssh root@192.168.5.1 "uci get tailscale.settings.fw_mode"
# Должно быть: none

# 4. Проверить rc.local
ssh root@192.168.5.1 "grep tailscaled /etc/rc.local"
# Должен быть: tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking

# 5. Проверить init.d
ssh root@192.168.5.1 "/etc/init.d/tailscale enabled && echo ENABLED || echo DISABLED"
# Должно быть: DISABLED

# 6. Применить fix-tailscale-openwrt.sh
cat ~/CLAUDECODE/fix-tailscale-openwrt.sh | ssh root@192.168.5.1 sh -s

# 7. Если всё равно не работает — ручной перезапуск
ssh root@192.168.5.1 "
killall tailscaled 2>/dev/null
tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
sleep 3
tailscale up --accept-dns=false --accept-routes
"
```

---

## 9. Формат отчёта в чате

При прошивке нового роутера **каждый шаг выводится в чат** с:
- ✅ зелёная галочка — успех
- ❌ красный крест — ошибка (СТОП)
- ⏱ тайминг — сколько времени занял шаг
- 📊 итоговая таблица в конце

### 9.1 Пример вывода шага

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ШАГ 1: Заливка OpenWrt 25.12.2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⏱ 2 мин 15 сек
  📍 192.168.1.1 → 192.168.1.1
  📦 openwrt-25.12.2-xiaomi_mi-router-ax3000t-squashfs-sysupgrade.bin
  ✅ WAN: IP получен (100.x.x.x)
  ✅ Пинг 1.1.1.1: 0% loss
  ✅ Пинг google.com: 0% loss
```

### 9.2 Пример ошибки

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ ШАГ 3: Применить шаблон
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⏱ 1 мин 30 сек
  ❌ WAN: IP не получен!
  ❌ Пинг 1.1.1.1: 100% loss
  ⛔ СТОП! Шаблон сломал network config.
  🔧 Диагностика: ubus call network.interface.wan status
```

### 9.3 Итоговая таблица в конце

После завершения всех шагов выводится таблица:

```
╔══════════════════════════════════════════════════════════╗
║           📊 ИТОГ ПРОШИВКИ: <ROUTER_NAME>               ║
╠══════════════════════════════════════════════════════════╣
║  Шаг 0: Проверка роутера          ⏱ 0:15  ✅           ║
║  Шаг 1: Заливка 25.12.2           ⏱ 2:15  ✅           ║
║  Шаг 2: Создание backup-шаблона   ⏱ 0:30  ✅           ║
║  Шаг 3: Применить шаблон          ⏱ 1:30  ✅           ║
║  Шаг 4: Создать ключ main         ⏱ 1:00  ✅           ║
║  Шаг 5: Установка Podkop          ⏱ 1:00  ✅           ║
║  Шаг 6: Настройка Podkop          ⏱ 0:20  ✅           ║
║  Шаг 7: Установка Tailscale       ⏱ 0:30  ✅           ║
║  Шаг 8: Спасительные скрипты      ⏱ 0:30  ✅           ║
║  Шаг 9: Tailscale авторизация     ⏱ 0:45  ✅           ║
║  Шаг 10: Проверка перед ребутом   ⏱ 0:10  ✅           ║
║  Шаг 11: Ребут                    ⏱ 2:00  ✅           ║
║  Шаг 12: Финальная диагностика    ║ 0:30  ✅           ║
╠══════════════════════════════════════════════════════════╣
║  ⏱ ОБЩЕЕ ВРЕМЯ:                  10 мин 45 сек         ║
║  🌐 Tailscale IP:                 100.x.x.x             ║
║  📍 LAN IP:                       192.168.5.1           ║
║  🟢 check-ip:                     loc=DE (Чехия)       ║
╚══════════════════════════════════════════════════════════╝
```

### 9.4 Правила форматирования

1. **Каждый шаг начинается с разделителя** `━━━` (25 символов)
2. **Заголовок шага** — жирный текст с номером
3. **Тайминг** — всегда `⏱ X мин X сек`
4. **WAN проверка** — всегда после шага (✅ или ❌)
5. **Ошибка** — сразу ❌ + причина + СТОП + что делать
6. **Итоговая таблица** — в конце, рамка из `║║╔╗╚╝╠╣`
7. **Общее время** — сумма всех шагов

---

*Последнее обновление: 2026-05-08*
