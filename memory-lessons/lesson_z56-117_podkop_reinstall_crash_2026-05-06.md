# Урок: Переустановка podkop на Z56-117 (Cudy WR3000H)
**Дата:** 06.05.2026
**Роутер:** 100.87.253.107 (z56-117-s-rogachev)
**Модель:** Cudy WR3000H v1
**OpenWrt:** 25.12.0

## Проблема
Podkop был в ужасном состоянии — конфиги сломаны, sing-box-tiny вместо полного sing-box, скрипт install.sh не мог скачать пакеты с GitHub из-за блокировки Amazon S3 CDN провайдером.

## Решение

### Шаг 1: Полная очистка
```bash
# Остановить
/etc/init.d/podkop stop
killall sing-box

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

### Шаг 2: Установка полного sing-box
```bash
apk del sing-box-tiny
apk add sing-box
```

### Шаг 3: Скачивание podkop с компа (GitHub заблокирован на роутере)
```bash
# На локальном компе:
curl -sL "https://github.com/itdoginfo/podkop/releases/download/0.7.14/podkop-0.7.14-r1.apk" -o podkop-0.7.14-r1.apk

# Залить на роутер (важно: scp -O, т.к. sftp-server нет):
sshpass -p '56756789' scp -O podkop-0.7.14-r1.apk root@100.87.253.107:/tmp/podkop/
```

### Шаг 4: Установка podkop + luci
```bash
apk add --force-overwrite --allow-untrusted \
  /tmp/podkop/podkop-0.7.14-r1.apk \
  /tmp/podkop/luci-app-podkop-0.7.14-r1.apk \
  /tmp/podkop/luci-i18n-podkop-ru-0.7.14.apk
```

### Шаг 5: Создать директорию (баг в .apk)
```bash
mkdir -p /usr/lib/podkop
```

### Шаг 6: Настройка podkop
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
uci set podkop.main.proxy_string='vless://b10e856c-e7d4-4e7c-a06f-7b7c2e17e630@5.35.84.151:2090?type=grpc&security=reality&mode=gun&serviceName=&pbk=OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI&sid=c30f9fec74087d32&sni=www.apple.com&fp=chrome&spx=%2F#wbr-03_Main'

# 20 community списков (telegram и meta — первыми!)
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
uci set podkop.YT.proxy_string='vless://c4549530-e8c2-4794-be9f-d7b034212e0e@159.194.198.172:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI&sid=1cbf0359&sni=www.apple.com&fp=chrome&spx=%2F#podkop_YT_8853_bMSK'

# 1 community список — только youtube
uci add_list podkop.YT.community_lists='youtube'

# ===== СОХРАНИТЬ =====
uci commit podkop
```

### Шаг 7: Запуск
```bash
/etc/init.d/podkop restart
```

## 🚨 Почему 3 дня ничего не получалось

### Корень: `download_lists_via_proxy=1`

Когда я в первый раз настроил podkop, я включил `download_lists_via_proxy=1`. Podkop 0.7.14 при этой настройке добавляет в каждый rule_set `"download_detour": "-out"`. Но outbound с тегом `-out` не существует. Sing-box падает с FATAL:

```
FATAL[0000] start service: (initialize rule-set[0]: download detour not found: -out | ...)
```

**Почему это не очевидно:** podkop пишет в лог `[info] sing-box configuration is unchanged` или `[info] Configure the route section`, но sing-box молча падает. Только если смотреть `logread | grep FATAL` — видно ошибку.

### Как решили: `download_lists_via_proxy=0`

Списки скачиваются напрямую (GitHub API доступен, блокируются только Amazon S3 CDN для .apk файлов).

### Вторая проблема: добавление всех 20 списков разом

Когда podkop получает сразу 20+ community_lists за один раз (особенно если до этого lists были пустыми), он может сгенерировать некорректный конфиг.

**Решение:** Добавлять списки поэтапно — группами по 5, проверяя после каждой группы что sing-box жив.

### Третья проблема: russia_inside

`russia_inside` — это список российских ресурсов, которые НЕ нужно проксировать. Он не нужен. Нужны 20 списков из инструкции выше.

## Текущий статус
- Podkop: ✅ running
- Sing-box: ✅ RUNNING
- LuCI: ✅ видит podkop в Services
- Main профиль: 20 community списков
- YT профиль: 1 community список (youtube)
- DNS: udp, 1.1.1.1
- download_lists_via_proxy: 0
- exclude_ntp: 1
- update_interval: 1h
- Tailscale: ✅ не тронут
- Диск: 13.3MB свободно (68% занято)
