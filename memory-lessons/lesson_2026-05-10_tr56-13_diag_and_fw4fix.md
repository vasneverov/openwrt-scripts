# Урок: tr56-13 — диагностика + fw4-fix (10.05.2026)

## Контекст
Роутер tr56-13 (Cudy TR3000 v1, OpenWrt 25.12.0, Билайн Москва).
Пришёл после прошивки — всё зелёное, но нужна полная диагностика и установка fw4-fix.

## Что сделано

### 1. Полная диагностика (11 пунктов)
- System, WAN, Provider, Proxy, Tailscale, Podkop, Sites, Ping, Watchdog, fw4-fix, rc.local
- **Прокси работает:** Италия (loc=IT), IP 151.243.198.86
- **Важные сайты:** google 301, youtube 301, telegram 200, x.com 200, discord 200 — все ✅
- **Ping не проходит** — ICMP блокируется (норма для прокси)

### 2. Установлены watchdog'ы
- `podkop-watchdog` — проверяет sing-box:1602, podkop alive, интернет
- `route-watchdog` — проверяет default gateway, FakeIP route, tailscale0 в LAN
- `ts-watchdog` — проверяет tailscaled alive
- Crontab: 4 watchdog'а + list_update

### 3. WAN firewall fix
- WAN зона существует, input=REJECT (нормально)

### 4. fw4-fix скрипт
- Создан `/root/podkop-fw4-fix.sh`
- Добавляет правило маркировки в `fw4 mangle_forward` после перезагрузки fw4
- Хук в `/etc/firewall.user` — выполняется при каждом fw4 reload
- После установки: 1 rule active ✅

### 5. Podkop enabled
- Был `"enabled":0,"status":"running but disabled"` — включён через `/etc/init.d/podkop enable`

## Проблемы, которые НЕ чинили (не критично)
- **rutracker.org 000** — заблокирован РКН, не наша проблема
- **github.com 502** — Bad Gateway, временная проблема GitHub
- **Ping не проходит** — ICMP через прокси не работает, норма

## Ошибки, которые допускали в процессе
1. **Podkop статус путал** — `get_sing_box_status` показывает `"enabled":0` даже когда podkop работает. Надо смотреть `get_status` — там `"enabled":1`.
2. **dnsmasq server формат** — `127.0.0.42` без `#53` работает, но `noresolv=1` может сломать DNS. Лучше не трогать dnsmasq если podkop уже работает.
3. **udhcpc при restart podkop** — podkop перезапускает udhcpc, что может временно сломать WAN. Не паниковать — DHCP сам восстановится.

## Ключевые выводы
- **Диагностика должна быть read-only** — сначала смотрим, потом чиним
- **Не трогать то, что работает** — dnsmasq, DNS, FakeIP — если podkop зелёный, не лезть
- **fw4-fix ставить всегда** — защита от сброса правил при fw4 reload
- **Watchdog'ы ставить всегда** — 3 шт минимум (ts, podkop, route)
- **Проверять podkop enabled** — `get_status` а не `get_sing_box_status`

## Связанные файлы
- `ROUTERS_REPAIRED_BASE.md` — строка #32
- `.claude/skills/router-diag-step/SKILL.md` — универсальная диагностика
