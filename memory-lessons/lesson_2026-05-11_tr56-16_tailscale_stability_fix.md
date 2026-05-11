# Урок: Стабильность Tailscale после холодной перезагрузки (tr56-16)
## Дата: 2026-05-11
## Роутер: tr56-16 (Cudy TR3000 v1, OpenWrt 25.12.0, Tailscale 1.96.4)

---

## Проблема

После холодной перезагрузки (снятие/подача питания) Tailscale на tr56-16:
1. Поднимался (LAN +35с, Tailscale +35с)
2. Точка в админке Tailscale была зелёной
3. Через ~1 минуту точка становилась **серой**
4. ts-watchdog срабатывал через ~2 минуты и восстанавливал
5. Через 4 минуты мониторинга — стабильно зелёный

## Корень проблемы

**Не в userspace-networking!** userspace-networking — это нормальный режим для OpenWrt 25.12.0. Он работал идеально на всех прошитых роутерах до последних 3 дней.

**Реальная причина:** `tailscale up --reset` в rc.local не успевал завершиться до того как watchdog проверял состояние. Tailscale стартовал, но DERP-соединение не успевало установиться → точка серая → watchdog перезапускал → всё чинилось.

## Что было сделано для исправления

### 1. rc.local — правильный порядок запуска
```sh
#!/bin/sh

# === TAILSCALE STARTUP ===
tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
sleep 3
tailscale up --reset --accept-dns=false --accept-routes --hostname=tr56-16 --netfilter-mode=off &

# === WATCHDOG ===
/etc/ts-watchdog.sh &

logger -t rc.local 'rc.local complete'
ip route add 198.18.0.0/15 dev lo 2>/dev/null

exit 0
```

**Ключевые элементы:**
- `tailscaled` стартует ПЕРВЫМ (без него tailscale up не работает)
- `sleep 3` — дать tailscaled время инициализироваться
- `tailscale up --reset` — чистая авторизация (сбрасывает кеш)
- `--netfilter-mode=off` — не трогать iptables (иначе убивает маршрутизацию)
- `ip route add 198.18.0.0/15 dev lo` — FakeIP route для DNS
- ts-watchdog в фоне — авто-восстановление

### 2. ts-watchdog — 3 проверки
```sh
#!/bin/sh

LOCKFILE=/tmp/ts-watchdog.lock

# Lock guard
if [ -f "$LOCKFILE" ]; then
    LOCKPID=$(cat "$LOCKFILE" 2>/dev/null)
    if kill -0 "$LOCKPID" 2>/dev/null; then
        exit 0
    fi
fi
echo $$ > "$LOCKFILE"

# CHECK 1: tailscaled running
if ! ps | grep -q "tailscaled --state="; then
    logger -t ts-watchdog "tailscaled not running, restarting..."
    tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
    sleep 5
    tailscale up --accept-dns=false --accept-routes &
    logger -t ts-watchdog "tailscaled restarted"
    rm -f "$LOCKFILE"
    exit 0
fi

# CHECK 2: NoState fix (tailscale up stuck)
TS_STATE=$(tailscale status --json 2>/dev/null | grep '"BackendState"' | cut -d'"' -f4)
if [ "$TS_STATE" = "NoState" ]; then
    logger -t ts-watchdog "NoState detected, restarting tailscaled..."
    killall tailscale 2>/dev/null
    killall tailscaled 2>/dev/null
    sleep 2
    tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
    sleep 5
    tailscale up --accept-dns=false --accept-routes &
    logger -t ts-watchdog "tailscaled restarted from NoState"
fi

# CHECK 3: DERP connection
if ! tailscale status 2>/dev/null | grep -q '100\.'; then
    logger -t ts-watchdog "No Tailscale IP, reconnecting..."
    tailscale up --accept-dns=false --accept-routes &
    logger -t ts-watchdog "tailscale up re-issued"
fi

rm -f "$LOCKFILE"
```

### 3. enable_udp_over_tcp
```sh
tailscale set --prefer-udp-over-tcp=false
```
По умолчанию UDP over TCP включён. Не нужно явно включать.

## Результаты теста холодной перезагрузки

| Этап | Время |
|------|-------|
| Питание отключено | 10:55:30 |
| Питание подано | ~10:55:40 |
| LAN появился | +14с |
| Tailscale в сети | +35с |
| Интернет работает | +35с |
| Ping до tr-boss-00 | +35с (2ms direct) |

**4-минутный мониторинг: 8/8 — все зелёные. 0 сбоев.**

## Что проверять при диагностике Tailscale

```sh
# 1. Статус Tailscale
tailscale status

# 2. JSON статус (TUN, BackendState)
tailscale status --json | grep -E '"TUN"|"BackendState"|"Version"'

# 3. DERP соединения
tailscale netcheck

# 4. Логи tailscaled
cat /tmp/ts.log | grep -i 'health\|derp\|error\|fail\|lost'

# 5. Проверка tailscale0 интерфейса
ip addr show tailscale0 2>/dev/null | grep 'inet '

# 6. FakeIP route
ip route show 198.18.0.0/15

# 7. rc.local
cat /etc/rc.local

# 8. ts-watchdog
cat /etc/ts-watchdog.sh
```

## Важно: userspace-networking — НЕ проблема

- `"TUN": false` — это НОРМАЛЬНО для OpenWrt 25.12.0
- tailscale0 интерфейс НЕ создаётся в userspace-режиме — это норма
- Все прошитые роутеры работают в userspace-networking
- Проблема была в отсутствии watchdog с NoState fix и неправильном порядке в rc.local

## Что должно быть на каждом роутере

1. **rc.local** с правильным порядком: tailscaled → sleep → tailscale up --reset → watchdog
2. **ts-watchdog** с 3 проверками: tailscaled running, NoState, DERP connection
3. **FakeIP route**: `ip route add 198.18.0.0/15 dev lo`
4. **enable_udp_over_tcp**: по умолчанию включён (не менять)
5. **init.d tailscale DISABLED**: `service tailscale disable` (чтобы не стартовал раньше сети)
