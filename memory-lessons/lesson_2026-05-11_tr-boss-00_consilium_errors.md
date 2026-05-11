# Урок: tr-boss-00 — консилиум и разбор ошибок

## Ситуация
Роутер Cudy TR3000 v1 (tr-boss-00). Уже прошит пользователем. Нужно: настроить podkop, авторизовать tailscale на учётку 4, поставить спасительные скрипты.

## Ошибки

### 1. Не загрузил скилл flash_router_universal.md
- **Что сделал:** начал действовать сам, без скилла
- **Надо было:** загрузить flash_router_universal.md, взять шаги 7 (tailscale авторизация) и 8 (спасительные скрипты)
- **Последствие:** пропустил pre-auth key, ожидание зелёной точки ping-циклом, спасительные скрипты

### 2. Не поставил direct_domains для tailscale ДО авторизации
- **Что сделал:** пытался сделать tailscale up без direct_domains
- **Надо было:** сначала добавить tailscale.com, controlplane.tailscale.com, login.tailscale.com в direct_domains podkop
- **Последствие:** tailscale up висел, не мог достучаться до controlplane через прокси

### 3. Использовал nohup на OpenWrt
- **Что сделал:** написал `nohup tailscale up ...`
- **Надо было:** `(tailscale up ... &)` или просто `tailscale up ... &`
- **Последствие:** nohup: not found, tailscale up не запустился

### 4. Не проверил fw_mode и init.d после установки
- **Что сделал:** не проверил uci tailscale.settings.fw_mode и /etc/init.d/tailscale enabled
- **Надо было:** сразу после tailscale up проверить и исправить
- **Последствие:** fw_mode=nftables (должно быть none), init.d=ENABLED (должно быть DISABLED)

### 5. Не загрузил спасительные скрипты сразу
- **Что сделал:** не поставил rc.local, watchdog, fw4-fix, fix-lists
- **Надо было:** ставить одной пачкой сразу после tailscale up
- **Последствие:** без них после ребута tailscale не поднимется, списки не обновятся

## Правила на будущее

### Железное правило: Всегда загружать скилл
При любой работе с роутером — загрузить flash_router_universal.md. Даже если прошивка не нужна, брать шаги 7-8-9-10-11.

### Железное правило: direct_domains для tailscale
Перед tailscale up обязательно:
```
uci add_list podkop.settings.direct_domains='tailscale.com'
uci add_list podkop.settings.direct_domains='controlplane.tailscale.com'
uci add_list podkop.settings.direct_domains='login.tailscale.com'
uci commit podkop
/etc/init.d/podkop restart
```

### Железное правило: Спасительные скрипты одной пачкой
После tailscale up сразу ставить:
1. rc.local (tailscaled → sleep → tailscale up --reset → watchdog)
2. ts-watchdog.sh v3.1 (NoState fix + lock-файл)
3. podkop-watchdog.sh + route-watchdog.sh
4. crontab (3 watchdog'а каждые 2 мин + list_update каждые 3ч)
5. podkop-fw4-fix.sh install
6. podkop-fix-lists.sh
7. check-ip скрипт

### Железное правило: Проверка после tailscale up
```
uci get tailscale.settings.fw_mode  # должно быть 'none'
/etc/init.d/tailscale enabled       # должно быть DISABLED
```

### Железное правило: Списки podkop
Списки ставить в порядке приоритета:
```
telegram, meta, youtube — первые
geoblock, block, porn, news, anime, discord, twitter, tiktok, cloudflare, google_ai, google_play, hodca, roblox, hetzner, ovh, digitalocean, cloudfront — остальные
```
Всего 21 список. Порядок важен — telegram/meta/youtube имеют приоритет.

## Результат
- Tailscale: 100.67.82.5, ONLINE ✅
- Прокси: loc=CZ ✅
- Сайты: все 200/301 ✅
- Watchdog: 3 шт каждые 2 мин ✅
- fw4-fix: 922 правила ✅
- fw_mode: none ✅
- init.d: DISABLED ✅
