# Алгоритм диагностики podkop (для любой LLM)

> **Цель:** Универсальный алгоритм, по которому любая модель (Claude, GPT, DeepSeek и т.д.) может диагностировать и чинить podkop на OpenWrt роутере.
>
> **Автор:** vas.neverov
> **Дата:** 2026-05-07
> **Проверено на:** tr56-09 (Teleservis, Жуковский), z56-84 (MTS, Москва)

---

## 1. Быстрая проверка (1 минута)

Подключиться к роутеру и выполнить:

```bash
# 1. sing-box жив?
pgrep -a sing-box

# 2. Tailscale жив?
tailscale status | head -3

# 3. Маршрутизация работает?
for url in google.com youtube.com telegram.org facebook.com instagram.com; do
  printf "%-15s %3s %s\n" "$url" \
    "$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://$url 2>/dev/null)" \
    "$(curl -s -o /dev/null -w '%{remote_ip}' --max-time 8 https://$url 2>/dev/null)"
done

# 4. Логи podkop
logread -e podkop | tail -20
```

**Признаки здоровья:**
- ✅ sing-box запущен (один процесс)
- ✅ Tailscale показывает соседние роутеры
- ✅ youtube/telegram/facebook → IP вида `198.18.0.x` (идут через podkop)
- ✅ google.com → реальный IP (идёт напрямую)
- ✅ В логах нет `[warn]` и `[error]`

---

## 2. Если листы не обновляются

**Симптом:** В логах podkop:
```
[warn] Attempt 1/3 to download http://127.0.0.1/Subnets/IPv4/telegram.lst failed
```

**Причина:** Провайдер блокирует `raw.githubusercontent.com` (частично или полностью).

### Диагностика

```bash
# Проверить DNS
nslookup raw.githubusercontent.com

# Проверить ping
ping -c 2 185.199.108.133

# Проверить curl (обычный)
curl -sL -o /dev/null -w "HTTP %{http_code} Time: %{time_total}s\n" \
  --max-time 10 "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Subnets/IPv4/meta.lst"

# Проверить каждый IP Fastly CDN
for ip in 185.199.108.133 185.199.109.133 185.199.110.133 185.199.111.133; do
  echo -n "$ip → "
  curl -sL --max-time 5 --resolve "raw.githubusercontent.com:443:$ip" \
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Subnets/IPv4/meta.lst" \
    -o /dev/null -w "HTTP %{http_code}\n"
done
```

### Лечение

```bash
# Запустить скрипт (скачать с репозитория)
wget -q -O /root/podkop-fix-lists.sh \
  "https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fix-lists.sh"
chmod +x /root/podkop-fix-lists.sh
sh /root/podkop-fix-lists.sh

# Или вручную добавить рабочие IP в /etc/hosts
echo "185.199.108.133 raw.githubusercontent.com" >> /etc/hosts
echo "185.199.109.133 raw.githubusercontent.com" >> /etc/hosts

# Перезапустить обновление листов
podkop list_update
```

### Добавить в cron

```bash
echo "0 3 * * * /bin/sh /root/podkop-fix-lists.sh --cron" >> /etc/crontabs/root
```

---

## 3. Если sing-box не запускается

**Симптом:** `pgrep -a sing-box` ничего не показывает.

### Диагностика

```bash
# Логи sing-box
logread -e sing-box | tail -20

# Проверить конфиг
sing-box check -c /etc/sing-box/config.json 2>&1

# Проверить mixed_proxy (частая проблема)
uci get podkop.main.mixed_proxy_enabled
```

### Лечение

```bash
# Если mixed_proxy_enabled=1 — выключить
uci set podkop.main.mixed_proxy_enabled=0
uci commit podkop
/etc/init.d/podkop reload

# Если конфиг битый — перегенерировать
/etc/init.d/podkop restart
```

---

## 4. Если community rule-sets (.srs) не обновляются

**Симптом:** В логах podkop нет ошибок, но .srs файлы старые.

**Важно:** .srs файлы качаются **sing-box**, а не podkop. Sing-box качает их с `github.com/itdoginfo/allow-domains/releases/latest/download/`. Если `github.com` доступен — .srs обновляются автоматически.

### Проверка

```bash
# Проверить доступность github.com
curl -sL -o /dev/null -w "HTTP %{http_code}\n" \
  --max-time 10 "https://github.com/itdoginfo/allow-domains/releases/latest/download/telegram.srs"

# Посмотреть .srs файлы
ls -la /www/srs/
```

---

## 5. Если клиентские устройства не работают

**Симптом:** С роутера всё пингуется, но клиенты (WiFi/LAN) не выходят в интернет.

### Диагностика

```bash
# Проверить DNS на клиентах
# Должен быть 192.168.1.1 (роутер)

# Проверить NAT/masquerade
iptables -t nat -L -n 2>/dev/null | grep MASQUERADE

# Проверить DHCP
cat /tmp/dhcp.leases

# Проверить firewall
iptables -L -n 2>/dev/null | head -20
```

---

## 6. Полный сброс podkop

Если ничего не помогает:

```bash
# Сбросить настройки
uci set podkop.main.mixed_proxy_enabled=0
uci set podkop.settings.download_lists_via_proxy=0
uci set podkop.settings.download_community_lists_via_proxy=0
uci commit podkop

# Перезапустить
/etc/init.d/podkop reload

# Проверить логи
logread -e podkop | tail -30
```

---

## 7. Полезные команды

```bash
# Версия podkop
podkop --version 2>/dev/null || opkg list-installed | grep podkop

# Версия sing-box
sing-box version 2>/dev/null

# Статус podkop
/etc/init.d/podkop status

# Логи podkop в реальном времени
logread -f -e podkop

# Список всех community листов
ls /www/srs/

# Список всех subnet листов
ls /www/Subnets/IPv4/

# Текущий конфиг podkop
uci show podkop
```

---

## 8. История: что было сделано на tr56-09

**Проблема:** Podkop не обновлял community subnet листы.
**Причина:** Провайдер Teleservis блокирует 2 из 4 IP Fastly CDN (185.199.110.133, 185.199.111.133).
**Решение:** Добавлены рабочие IP (185.199.108.133, 185.199.109.133) в `/etc/hosts`.
**Скрипт:** `podkop-fix-lists.sh` — автоматически проверяет все 4 IP и добавляет только рабочие.
**Cron:** `0 3 * * * /bin/sh /root/podkop-fix-lists.sh --cron`
**Урок:** `memory-lessons/lesson_raw_github_block_fix_2026-05-07.md`

---

## 9. ДИАГНОСТИКА: forwarded трафик (клиенты WiFi/LAN)

**Главный вопрос:** Видит ли podkop трафик от клиентов (ноутбуки, телефоны) или только с самого роутера?

### Почему это важно

На OpenWrt 25.12+ (fw4/nftables) таблица `inet PodkopTable` с `hook prerouting` **может не видеть forwarded трафик** (с клиентов WiFi/LAN). Она видит только local трафик (с самого роутера).

**Симптом:** С роутера через SSH `curl https://2ip.ru` показывает нужную страну, а клиенты за роутером видят Россию.

### Диагностика forwarded трафика

```bash
# 1. Проверить, есть ли forwarded трафик в PodkopTable
echo "=== Счётчики PodkopTable mangle (prerouting) ==="
nft list chain inet PodkopTable mangle 2>/dev/null | grep "counter" | head -5

# 2. Проверить, есть ли forwarded трафик в fw4 mangle_forward
echo "=== Счётчики fw4 mangle_forward ==="
nft list chain inet fw4 mangle_forward 2>/dev/null | grep "counter" | head -5

# 3. Проверить счётчики TPROXY
echo "=== Счётчики PodkopTable proxy ==="
nft list chain inet PodkopTable proxy 2>/dev/null | grep "counter"
```

### Интерпретация результатов

| Ситуация | PodkopTable mangle | fw4 mangle_forward | Вывод |
|---|---|---|---|
| ✅ Всё работает | packets > 0 | packets > 0 (или есть podkop-fw4-fix) | Всё ок |
| ⚠️ Только local | packets > 0 | packets = 0, нет podkop-fw4-fix | **Нужен podkop-fw4-fix** |
| ❌ Ничего не работает | packets = 0 | packets = 0 | Проблема не в forwarded, копать дальше |

### Финальная проверка (обязательно!)

После прошивки или ремонта — **всегда проверять IP с клиента**, а не только с роутера!

```bash
# Проверка с роутера (через SSH) — показывает OUTPUT трафик
echo "=== С роутера (OUTPUT) ==="
curl -s --connect-timeout 5 --max-time 10 https://2ip.ru | head -3
curl -s --connect-timeout 5 --max-time 10 https://myip.ipip.net

# Проверка с клиента (FORWARD) — самый надёжный способ
# Подключиться к WiFi роутера и открыть в браузере:
#   https://2ip.ru
#   https://myip.ipip.net
#   https://whoer.net

# Если нет доступа к клиенту — проверить счётчики nftables
echo "=== Счётчики mangle_forward ==="
nft list chain inet fw4 mangle_forward 2>/dev/null | grep "counter"
```

### Критерии успеха

| Проверка | Ожидаемый результат |
|---|---|
| **2ip.ru** (с роутера) | Страна НЕ Россия |
| **2ip.ru** (с клиента) | Страна НЕ Россия |
| **myip.ipip.net** (с клиента) | Страна НЕ Россия |
| **ipinfo.io** | 🇷🇺 Россия (этот сайт не в списках podkop) |

---

## 10. СПЯЩИЕ АГЕНТЫ: три скрипта, которые ставятся на роутер

**Важно:** "Спящие агенты" — это скрипты, которые живут на роутере и автоматически чинят проблемы. Не путать между собой. У каждого своё назначение.

### Спасительный — `rescue_generic.sh`
**Файл:** `rescue_generic.sh` (в корне репозитория на GitHub)
**Назначение:** Базовая стабилизация роутера. Применяется когда роутер "сыпется" — Tailscale отваливается, часы дрейфуют, podkop падает.
**Что делает:**
- `fw_mode=none` — иначе Tailscale убивает маршрутизацию
- `init.d/tailscale DISABLED` — иначе при ребуте Tailscale стартует раньше сети
- `exclude_ntp=1` — иначе NTP ломает синхронизацию
- `rc.local` с tailscaled (sleep 40)
- **3 watchdog'а на 2 минуты:**
  - `ts-watchdog.sh` — следит за tailscaled, восстанавливает rc.local
  - `podkop-watchdog.sh` — следит за sing-box, перезапускает podkop если упал
  - `route-watchdog.sh` — следит за PodkopTable в nftables
- Crontab со всеми watchdog'ами + обновление списков каждые 3 часа

**Запуск:**
```bash
cat rescue_generic.sh | ssh root@ROUTER_IP sh -s
```

### Листовой скрипт — `podkop-fix-lists.sh`
**Файл:** `tools/podkop-fix-lists.sh`
**Назначение:** Фикс блокировки GitHub CDN. Применяется когда провайдер блокирует `raw.githubusercontent.com` и podkop не может скачать списки.
**Что делает:**
- Проверяет все 4 IP Fastly CDN (185.199.108-111.133)
- Добавляет только рабочие IP в `/etc/hosts`
- Может работать в cron режиме (`--cron`)

**Запуск:**
```bash
wget -q -O /root/podkop-fix-lists.sh \
  "https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fix-lists.sh"
chmod +x /root/podkop-fix-lists.sh
sh /root/podkop-fix-lists.sh
```

### fw4-fix скрипт — `podkop-fw4-fix.sh`
**Файл:** `tools/podkop-fw4-fix.sh`
**Назначение:** Фикс forwarded трафика на OpenWrt 25.12+. Применяется когда с роутера podkop работает, а с клиентов — нет.
**Что делает:**
- Копирует подсети из `inet PodkopTable podkop_subnets` в `inet fw4 podkop_subnets_fwd`
- Добавляет правила маркировки в `inet fw4 mangle_forward` (hook forward)
- Создаёт init.d автозапуск (S99podkop-fw4-fix)

**Запуск:**
```bash
cat tools/podkop-fw4-fix.sh | ssh root@ROUTER_IP "cat > /root/podkop-fw4-fix.sh && chmod +x /root/podkop-fw4-fix.sh"
ssh root@ROUTER_IP "/root/podkop-fw4-fix.sh install"
```

---

## 11. ПРИНЯТИЕ РЕШЕНИЯ: что и когда применять

На основе диагностики (шаги 1-9) выбираем вариант:

### Вариант A: Всё работает, ничего не нужно
**Условие:** С роутера и с клиента 2ip.ru показывает нужную страну. Логи чистые.
**Действие:** Ничего не делать. Задокументировать что всё ок.

### Вариант B: Нужен спасительный скрипт
**Условие:** Роутер нестабилен — Tailscale отваливается, часы дрейфуют, podkop падает.
**Решение:** Применить `rescue_generic.sh`.

```bash
cat rescue_generic.sh | ssh root@ROUTER_IP sh -s
```

### Вариант C: Нужен листовой скрипт
**Условие:** В логах podkop ошибки скачивания листов (`download failed`).
**Причина:** Провайдер блокирует `raw.githubusercontent.com`.
**Решение:** Установить `podkop-fix-lists.sh`.

```bash
wget -q -O /root/podkop-fix-lists.sh \
  "https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fix-lists.sh"
chmod +x /root/podkop-fix-lists.sh
sh /root/podkop-fix-lists.sh
echo "0 3 * * * /bin/sh /root/podkop-fix-lists.sh --cron" >> /etc/crontabs/root
```

### Вариант D: Нужен fw4-fix скрипт
**Условие:** С роутера 2ip.ru показывает нужную страну, но с клиента — Россия.
**Причина:** `inet PodkopTable prerouting` не видит forwarded трафик на OpenWrt 25.12.
**Решение:** Установить `podkop-fw4-fix.sh`.

```bash
cat tools/podkop-fw4-fix.sh | ssh root@ROUTER_IP "cat > /root/podkop-fw4-fix.sh && chmod +x /root/podkop-fw4-fix.sh"
ssh root@ROUTER_IP "/root/podkop-fw4-fix.sh install"
```

### Вариант E: Комбинация скриптов
**Условие:** Несколько проблем одновременно.
**Порядок применения:**
1. Сначала **спасительный скрипт** — стабилизирует роутер
2. Потом **листовой скрипт** — чинит скачивание списков
3. Потом **fw4-fix скрипт** — чинит forwarded трафик

---

## 12. WAN ifname — частая причина неработающего podkop

**Симптом:** Podkop запущен, сайты работают, но `check-ip` показывает российский IP даже через прокси. В таблице podkop только `local default dev lo scope host`.

**Причина:** Podkop использует `uci get network.wan.ifname` для определения WAN-интерфейса. Если в конфиге сети указан `device` вместо `ifname` — podkop не видит WAN и ставит заглушку.

### Диагностика

```bash
# Проверить ifname
uci get network.wan.ifname
# Если пусто — проблема!

# Проверить таблицу podkop
ip route show table podkop
# Должно быть: default via GATEWAY dev IFACE
# Если: local default dev lo scope host — проблема!

# Проверить device
uci get network.wan.device
# Обычно eth0 или подобное
```

### Лечение

```bash
# Добавить ifname (равный device)
uci set network.wan.ifname='eth0'  # заменить на актуальный интерфейс
uci commit network

# Перезапустить podkop
/etc/init.d/podkop restart

# Проверить таблицу
ip route show table podkop
# Должно быть: default via GATEWAY dev IFACE
```

### Где искать WAN интерфейс

```bash
# 1. Посмотреть конфиг сети
cat /etc/config/network | grep -A5 'config interface.*wan'

# 2. Посмотреть активные интерфейсы
ip addr show | grep -E '^[0-9]|inet '

# 3. Посмотреть default route
ip route show default
# default via 192.168.1.1 dev eth0 → WAN это eth0
```

### Профилактика

В `rescue_generic.sh` добавить проверку и добавление `network.wan.ifname`:
```bash
# Проверить и добавить ifname для WAN
WAN_IFNAME=$(uci get network.wan.ifname 2>/dev/null)
if [ -z "$WAN_IFNAME" ]; then
    WAN_DEVICE=$(uci get network.wan.device 2>/dev/null)
    if [ -n "$WAN_DEVICE" ]; then
        uci set network.wan.ifname="$WAN_DEVICE"
        uci commit network
        echo "  ✓ network.wan.ifname=$WAN_DEVICE (добавлен)"
    fi
fi
```

---

## 13. Community lists — проверка и обновление

**Симптом:** Podkop запущен, но `check-ip` показывает российский IP. Счётчики nftables `@podkop_subnets` = 0.

**Причина:** Community lists не загружены. Podkop не знает, какие IP проксировать.

### Диагностика

```bash
# Проверить, загружены ли списки
find /etc/podkop/ -type f
# Если пусто — списки не загружены

# Проверить настройки загрузки
uci get podkop.settings.download_community_lists_via_proxy
uci get podkop.settings.download_lists_via_proxy

# Проверить обновление списков
podkop list_update
# Смотреть ошибки:
# - "Failed to send request: Operation not permitted" → проблема с прокси
# - "Downloading 'http://127.0.0.1/..." → качает через себя (неправильно)
```

### Лечение

```bash
# 1. Отключить загрузку через прокси
uci set podkop.settings.download_community_lists_via_proxy='0'
uci set podkop.settings.download_lists_via_proxy='0'
uci commit podkop

# 2. Принудительно обновить списки
podkop list_update

# 3. Перезапустить podkop
/etc/init.d/podkop restart

# 4. Проверить, что списки загрузились
find /etc/podkop/ -type f
# Должны появиться файлы .lst
```

### Почему download_lists_via_proxy=1 не работает

Podkop пытается скачать списки через `http://127.0.0.1/Subnets/IPv4/...`. Это работает только если на роутере запущен HTTP-сервер, который раздаёт эти файлы. Sing-box **не является** HTTP-сервером. Поэтому `download_lists_via_proxy=1` вызывает ошибку `Failed to send request: Operation not permitted`.

**Правильная настройка:** `download_lists_via_proxy=0` — списки качаются напрямую с GitHub через WAN.

---

## 14. check-ip — правильные сервисы для проверки

**Важно:** `enable_output_network_interface=1` проксирует трафик ТОЛЬКО для IP из `@podkop_subnets` (community_lists). Сервисы определения IP должны входить в community_lists, иначе они покажут российский IP.

### Работающие сервисы (есть в community_lists)

| Сервис | Community list | IP диапазон |
|---|---|---|
| `cloudflare.com/cdn-cgi/trace` | cloudflare | 104.16.0.0/12, 172.64.0.0/13 |
| `ident.me` | hetzner | 65.108.0.0/15 |
| `checkip.amazonaws.com` | cloudfront | 198.18.0.0/15 (fake IP) |

### НЕ работают (нет в community_lists)

| Сервис | Почему |
|---|---|
| `ifconfig.co` | Cloudflare, но домена нет в community_lists |
| `ifconfig.me` | Google Cloud, нет в списках |
| `ipinfo.io` | Google Cloud, нет в списках |
| `api.ipify.org` | Свой IP, нет в списках |

### Правильный check-ip скрипт

```bash
#!/bin/sh
echo '=== ЧЕРЕЗ ПРОКСИ (как LAN-клиент) ==='
echo '--- cloudflare.com/cdn-cgi/trace ---'
curl -s --connect-timeout 5 --max-time 10 https://cloudflare.com/cdn-cgi/trace | grep -E 'ip=|loc='
echo '--- ident.me ---'
curl -s --connect-timeout 5 --max-time 10 https://ident.me

echo ''
echo '=== НАПРЯМУЮ (с роутера) ==='
echo '--- ipinfo.io ---'
curl -s --connect-timeout 5 --max-time 10 https://ipinfo.io/json | grep -E '"ip"|"country"|"city"'
echo '--- ifconfig.me ---'
curl -s --connect-timeout 5 --max-time 10 https://ifconfig.me
```

---

## 15. Чеклист для прошивки/ремонта роутера

```bash
# 1. Подключиться по Tailscale
ssh root@<TAILSCALE_IP>

# 2. Быстрая проверка (шаг 1)
# 3. Если роутер нестабилен — спасительный скрипт (шаг 11, вариант B)
# 4. Если листы не обновляются — листовой скрипт (шаг 11, вариант C)
# 5. Если sing-box не стартует — проверить mixed_proxy (шаг 3)
# 6. ФИНАЛЬНАЯ ПРОВЕРКА: проверить IP с роутера И с клиента (шаг 9)
# 7. Если с клиента не работает — fw4-fix скрипт (шаг 11, вариант D)
# 8. Сохранить урок в memory-lessons/
```

---

*Последнее обновление: 2026-05-08*



