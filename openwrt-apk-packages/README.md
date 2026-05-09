# Podkop — Полная переустановка на OpenWrt 25.12 (apk)

**Версия:** 0.7.14-r1  
**OpenWrt:** 25.12.0 (apk, не opkg!)  
**Роутер:** Cudy WR3000H / TR3000 / M3000  
**Дата:** 06.05.2026

---

## ⚠️ Железные правила перед началом

1. **Tailscale — спасать любой ценой.** Перед любой операцией убедись что Tailscale работает. Если сломаешь — роутер станет кирпичом.
2. **Не перезагружать роутер без подтверждения пользователя.**
3. **Перед опасной операцией — проверить SSH** (`echo ALIVE`).
4. **OpenWrt 25.12 = apk, не opkg.** Не путать пакетные менеджеры.
5. **Никогда не делать `tar -xzf data.tar.gz -C /`** — это ломает систему.
6. **Полный sing-box, не sing-box-tiny.** Podkop требует полный.

---

## Полная инструкция по переустановке

### Шаг 1: Диагностика перед началом

```bash
# Проверить версию OpenWrt
cat /etc/openwrt_release | grep DISTRIB_RELEASE

# Проверить что есть SSH
echo "ALIVE"

# Проверить Tailscale
tailscale status

# Текущее состояние podkop
/etc/init.d/podkop status
pgrep sing-box && echo "sing-box RUNNING" || echo "sing-box DEAD"
```

### Шаг 2: Полная очистка

```bash
# Остановить
/etc/init.d/podkop stop
killall sing-box 2>/dev/null
sleep 2

# Удалить пакеты
apk del podkop luci-app-podkop luci-i18n-podkop-ru luci-i18n-podkop sing-box sing-box-tiny

# Удалить все файлы и хвосты
rm -f /etc/config/podkop
rm -rf /etc/sing-box/
rm -rf /tmp/sing-box/
rm -f /usr/bin/podkop
rm -f /etc/init.d/podkop
rm -f /etc/podkop-watchdog.sh
rm -rf /www/luci-static/resources/view/podkop/
rm -f /usr/share/luci/menu.d/luci-app-podkop.json
rm -f /usr/share/rpcd/acl.d/luci-app-podkop.json
rm -f /etc/uci-defaults/50_luci-podkop
rm -f /usr/lib/lua/luci/i18n/podkop.ru.lmo
rm -f /etc/rc.d/S99podkop
rm -f /etc/uci-defaults/luci-i18n-podkop-ru
rm -f /overlay/upper/etc/rc.d/S99podkop
rm -f /overlay/upper/etc/uci-defaults/luci-i18n-podkop-ru
rm -rf /overlay/upper/usr/lib/podkop
rm -f /overlay/upper/root/backup/podkop.config.backup
rm -f /root/backup/podkop.config.backup
rm -f /tmp/.uci/podkop
rm -f /tmp/lock/procd_podkop.lock
```

### Шаг 3: Установка полного sing-box

```bash
# Удалить tiny если остался
apk del sing-box-tiny 2>/dev/null

# Установить полный sing-box
apk add sing-box

# Проверить версию
sing-box version
# Должно быть: 1.12.17 или новее
```

### Шаг 4: Скачивание podkop с компа

**Важно:** GitHub releases (Amazon S3 CDN) заблокированы на роутере. Скачиваем на локальный комп и заливаем через scp.

```bash
# На локальном компе:
curl -sL "https://github.com/itdoginfo/podkop/releases/download/0.7.14/podkop-0.7.14-r1.apk" -o podkop-0.7.14-r1.apk
curl -sL "https://github.com/itdoginfo/podkop/releases/download/0.7.14/luci-app-podkop-0.7.14-r1.apk" -o luci-app-podkop-0.7.14-r1.apk
curl -sL "https://github.com/itdoginfo/podkop/releases/download/0.7.14/luci-i18n-podkop-ru-0.7.14.apk" -o luci-i18n-podkop-ru-0.7.14.apk

# Создать папку на роутере
sshpass -p 'password' ssh root@ROUTER_IP 'mkdir -p /tmp/podkop'

# Залить на роутер (важно: scp -O, т.к. sftp-server нет)
sshpass -p 'password' scp -O podkop-0.7.14-r1.apk root@ROUTER_IP:/tmp/podkop/
sshpass -p 'password' scp -O luci-app-podkop-0.7.14-r1.apk root@ROUTER_IP:/tmp/podkop/
sshpass -p 'password' scp -O luci-i18n-podkop-ru-0.7.14.apk root@ROUTER_IP:/tmp/podkop/
```

### Шаг 5: Установка podkop + luci

```bash
# На роутере:
apk add --force-overwrite --allow-untrusted \
  /tmp/podkop/podkop-0.7.14-r1.apk \
  /tmp/podkop/luci-app-podkop-0.7.14-r1.apk \
  /tmp/podkop/luci-i18n-podkop-ru-0.7.14.apk

# Создать директорию (баг в .apk — не создаётся автоматически)
mkdir -p /usr/lib/podkop
```

### Шаг 6: Базовая настройка podkop (UCI)

```bash
# ===== НАСТРОЙКИ =====
uci set podkop.settings.dns_type='udp'
uci set podkop.settings.dns_server='1.1.1.1'
uci set podkop.settings.bootstrap_dns_server='1.1.1.1'
uci set podkop.settings.dns_rewrite_ttl='60'
uci set podkop.settings.update_interval='1h'
uci set podkop.settings.download_lists_via_proxy='0'
uci set podkop.settings.exclude_ntp='1'
uci set podkop.settings.log_level='warn'
uci set podkop.settings.disable_quic='0'
uci set podkop.settings.enable_yacd='0'
uci set podkop.settings.enable_output_network_interface='0'
uci set podkop.settings.enable_badwan_interface_monitoring='0'
uci set podkop.settings.dont_touch_dhcp='0'
uci set podkop.settings.shutdown_correctly='0'
uci set podkop.settings.config_path='/etc/sing-box/config.json'
uci set podkop.settings.cache_path='/tmp/sing-box/cache.db'

# ===== ПРОФИЛЬ MAIN =====
uci set podkop.main.connection_type='proxy'
uci set podkop.main.proxy_config_type='url'
uci set podkop.main.enable_udp_over_tcp='0'
uci set podkop.main.user_domain_list_type='disabled'
uci set podkop.main.user_subnet_list_type='disabled'
uci set podkop.main.mixed_proxy_enabled='0'

# Ключ Main
uci set podkop.main.proxy_string='vless://UUID@SERVER:PORT?type=grpc&security=reality&mode=gun&serviceName=&pbk=PUBLIC_KEY&sid=SHORT_ID&sni=www.apple.com&fp=chrome&spx=%2F#Main'

# ===== 20 COMMUNITY СПИСКОВ MAIN =====
# ВАЖНО: добавлять по одному, не все сразу!
uci add_list podkop.main.community_lists='telegram'
uci add_list podkop.main.community_lists='meta'
uci add_list podkop.main.community_lists='geoblock'
uci add_list podkop.main.community_lists='block'
uci add_list podkop.main.community_lists='porn'
uci add_list podkop.main.community_lists='news'
uci add_list podkop.main.community_lists='anime'
uci add_list podkop.main.community_lists='discord'
uci add_list podkop.main.community_lists='twitter'
uci add_list podkop.main.community_lists='hdrezka'
uci add_list podkop.main.community_lists='tiktok'
uci add_list podkop.main.community_lists='cloudflare'
uci add_list podkop.main.community_lists='google_ai'
uci add_list podkop.main.community_lists='google_play'
uci add_list podkop.main.community_lists='hodca'
uci add_list podkop.main.community_lists='roblox'
uci add_list podkop.main.community_lists='hetzner'
uci add_list podkop.main.community_lists='ovh'
uci add_list podkop.main.community_lists='digitalocean'
uci add_list podkop.main.community_lists='cloudfront'

# ===== ПРОФИЛЬ YT =====
uci set podkop.YT.connection_type='proxy'
uci set podkop.YT.proxy_config_type='url'
uci set podkop.YT.enable_udp_over_tcp='0'
uci set podkop.YT.user_domain_list_type='disabled'
uci set podkop.YT.user_subnet_list_type='disabled'
uci set podkop.YT.mixed_proxy_enabled='0'

# Ключ YT
uci set podkop.YT.proxy_string='vless://UUID@SERVER:PORT?type=grpc&security=reality&mode=gun&serviceName=&pbk=PUBLIC_KEY&sid=SHORT_ID&sni=www.apple.com&fp=chrome&spx=%2F#YT'

# 1 community список — только youtube
uci add_list podkop.YT.community_lists='youtube'

# ===== СОХРАНИТЬ =====
uci commit podkop
```

### Шаг 7: Запуск

```bash
# Запустить podkop
/etc/init.d/podkop restart

# Подождать 5-10 секунд
sleep 5

# Проверить статус
/etc/init.d/podkop status
pgrep sing-box && echo "sing-box RUNNING" || echo "sing-box DEAD"

# Проверить логи
logread | grep podkop | tail -10
```

### Шаг 8: Проверка DNS

```bash
# Должны вернуться IP адреса (198.18.x.x — fakeip)
nslookup telegram.org 127.0.0.1
nslookup youtube.com 127.0.0.1
nslookup google.com 127.0.0.1
```

---

## 🚨 Почему всё ломалось — критически важные ошибки

### Ошибка №1: `download_lists_via_proxy=1` (самая частая)

**Симптом:** sing-box падает с FATAL: `download detour not found: -out`

**Причина:** Podkop 0.7.14 при `download_lists_via_proxy=1` добавляет в каждый rule_set поле `"download_detour": "-out"`. Но outbound с тегом `-out` не существует. Sing-box не может запуститься.

**Решение:** `download_lists_via_proxy=0`. Списки скачиваются напрямую.

### Ошибка №2: Добавление всех 20 списков одной командой

**Симптом:** sing-box падает, podkop пишет `[info] Configure the route section` но sing-box мёртв.

**Причина:** Когда podkop получает сразу 20+ community_lists за один раз, он может сгенерировать некорректный конфиг (особенно если до этого lists были пустыми). 

**Решение:** Добавлять списки **поэтапно** — группами по 5, проверяя после каждой группы что sing-box жив:
```bash
# 1. telegram + meta
uci add_list podkop.main.community_lists='telegram'
uci add_list podkop.main.community_lists='meta'
uci commit podkop
/etc/init.d/podkop restart
# проверить pgrep sing-box

# 2. geoblock + block + porn + news
uci add_list podkop.main.community_lists='geoblock'
...
```

### Ошибка №3: `russia_inside` вместо правильных списков

**Симптом:** Не все нужные сайты работают через прокси.

**Причина:** `russia_inside` — это список российских ресурсов, которые НЕ нужно проксировать. Он не заменяет остальные списки.

**Решение:** Использовать 20 списков из инструкции выше. `russia_inside` не нужен.

### Ошибка №4: Неправильный порядок списков

**Симптом:** Telegram не открывается, хотя ключ рабочий.

**Причина:** Порядок списков влияет на приоритет правил маршрутизации. Telegram и meta должны быть первыми.

**Решение:** telegram и meta — всегда первыми в списке.

### Ошибка №5: UDP вместо TCP для DNS

**Симптом:** DNS не резолвится, сайты не открываются.

**Причина:** `dns_type='tcp'` может не работать с некоторыми провайдерами.

**Решение:** `dns_type='udp'` — работает стабильно.

---

## Спасительный скрипт (Watchdog)

Создать `/etc/podkop-watchdog.sh`:

```bash
#!/bin/sh

# Проверка sing-box
if ! pgrep sing-box >/dev/null 2>&1; then
    logger -t watchdog "sing-box dead, restarting podkop"
    /etc/init.d/podkop restart
fi

# Проверка tailscaled
if ! pgrep tailscaled >/dev/null 2>&1; then
    logger -t watchdog "tailscaled dead, restarting"
    /etc/init.d/tailscale start 2>/dev/null || tailscale up --accept-routes --accept-dns=false --netfilter-mode=none
fi
```

Добавить в crontab (каждые 2 минуты):

```bash
echo '*/2 * * * * /bin/sh /etc/podkop-watchdog.sh' >> /etc/crontabs/root
/etc/init.d/cron restart
```

---

## Проверка после установки

```bash
# 1. Podkop запущен?
/etc/init.d/podkop status

# 2. Sing-box запущен?
pgrep sing-box && echo "RUNNING" || echo "DEAD"

# 3. Сколько community списков?
uci show podkop.main.community_lists | grep -o "'[a-z_]*'" | wc -l
# Должно быть: 20

uci show podkop.YT.community_lists | grep -o "'[a-z_]*'" | wc -l
# Должно быть: 1

# 4. DNS работает?
nslookup telegram.org 127.0.0.1 | grep Address

# 5. Нет ошибок в логах?
logread | grep -E "FATAL|error" | grep -v "Download.*failed"
```
