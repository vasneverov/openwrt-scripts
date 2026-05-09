# Руководство по ремонту роутеров OpenWrt + Podkop + Tailscale

> **Для AI-агентов:** Читай этот файл ПЕРВЫМ при любом запросе на ремонт или диагностику роутера.
> Здесь собраны все ошибки прошлых сессий и точный порядок действий.

---

## Архитектура системы (необходимый минимум)

```
Клиент → Роутер (OpenWrt+podkop+sing-box) → bMSK (Москва, relay) → Fin4 (Финляндия, выход)
                                              └─→ bMSK:8853 → YouTube (прямой)
```

**Серверы relay:**
| Сервер | IP | Порты relay → Fin4 inbound |
|---|---|---|
| bMSK | 159.194.198.172 | 5223→Fin4:4191 (sid `4b929012`) |
| bMSK | 159.194.198.172 | 5228→Fin4:4192 (sid `ae2bfb99`) |
| bMSK (YT) | 159.194.198.172 | 8853 (прямой, без Fin4) |

**Fin4 inbound:** `pbk HfbTqAI...` (полный pbk — в MASTER_CREDENTIALS.md)

**ЖЕЛЕЗНОЕ ПРАВИЛО:** UUID зарегистрированный на Fin4:**4191** → ключ собирать через bMSK:**5223**. UUID на 4192 → через 5228. Перепутать = красный профиль при зелёном check_vless.

---

## Шаг 0 — Сбор информации ПЕРЕД действиями

**Никогда не начинать ремонт без этих данных:**

```bash
# 1. Найти роутер в базе
grep -r "router_name\|tailscale_ip" ~/.claude/projects/-Users-vas/memory/all_routers_full_base.md

# 2. Прочитать справочник серверов
cat ~/CLAUDECODE/SERVERS_RELAY_REFERENCE.md

# 3. Найти существующие ключи роутера
cat ~/CLAUDECODE/memory-lessons/xui_inbounds_registry.md | grep "router_name"
# ИЛИ
cat ~/.claude/projects/-Users-vas/memory/xui_inbounds_registry.md
```

**Порядок поиска информации (ключи, UUID, IP):**
1. `~/CLAUDECODE/ключи/` — VLESS ключи
2. `~/.claude/projects/-Users-vas/memory/` — вся база
3. `~/CLAUDECODE/MASTER_CREDENTIALS.md` — пароли SSH, pbk, sid
4. Только если нигде нет → создавать самому

**Никогда не спрашивать пользователя о том, что есть в рабочих папках.**

---

## Шаг 1 — Tailscale устойчивость (ПЕРВЫЙ ПРИОРИТЕТ)

> **Почему первым:** Роутер > 1000 км от тебя. Если сначала сломаешь Tailscale —
> потеряешь доступ навсегда до физического вмешательства. Подкоп подождёт.

### Проверка текущего состояния:

```bash
uci get tailscale.settings.fw_mode           # → none (обязательно)
/etc/init.d/tailscale enabled 2>&1 | grep -q "enabled" && echo ENA || echo DIS  # → DIS
grep -q tailscaled /etc/rc.local && echo OK || echo MISSING   # → OK
crontab -l | grep -q watchdog && echo OK || echo MISSING      # → OK
```

### Правильная схема (userspace-networking):

```bash
# 1. fw_mode = none
uci set tailscale.settings.fw_mode='none'
uci commit tailscale

# 2. init.d DISABLED
/etc/init.d/tailscale disable

# 3. rc.local с запуском
# Должно содержать (примерно):
# tailscaled --tun=userspace-networking --statedir=/etc/tailscale/ &
# sleep 10
# tailscale up --accept-dns=false --accept-routes
```

### Watchdog (обязательно):

```bash
# Проверить
crontab -l | grep watchdog

# Если нет — добавить
crontab -l > /tmp/cron.tmp
echo "*/3 * * * * /etc/ts-watchdog.sh" >> /tmp/cron.tmp
crontab /tmp/cron.tmp
```

### Содержимое /etc/ts-watchdog.sh:

```bash
#!/bin/sh
if ! pgrep tailscaled > /dev/null 2>&1; then
    tailscaled --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 &
    sleep 10
    tailscale up --accept-dns=false --accept-routes
fi
# Защита resolv.conf (если Tailscale его перезаписывает):
if ! readlink /etc/resolv.conf | grep -q dnsmasq; then
    ln -sf /tmp/resolv.conf.d/resolv.conf.auto /etc/resolv.conf 2>/dev/null || \
    ln -sf /var/run/dnsmasq/resolv.conf /etc/resolv.conf 2>/dev/null
fi
```

### ❌ Никогда не делать:
- `tailscale serve` в rc.local или watchdog — заблокирует SSH навсегда
- `--state=` вместо `--statedir=` — ломает сохранение состояния после ребута
- TUN-режим (без `--tun=userspace-networking`) — TUN device busy = kernel panic

---

## Шаг 2 — Диагностика podkop (после того как Tailscale защищён)

### Быстрая диагностика:

```bash
# Состояние
uci show podkop

# Профили (смотреть красный/зелёный не нужно — только UCI)
cat /etc/config/podkop

# Sing-box работает?
pgrep sing-box && echo RUNNING || echo DEAD

# DNS работает?
nslookup telegram.org 127.0.0.1
```

### Если профиль красный в LuCI:

**СТОП. Не лезь в sing-box, логи, nft правила.**
→ Сразу создавать новый ключ (Шаг 3).

Красный = проблема в ключе (UUID не зарегистрирован / истёк / неверный relay порт).
Диагностика sing-box — потеря времени.

---

## Шаг 3 — Создание VLESS ключей

### Алгоритм (строго по порядку):

**1. Проверить готовые скрипты:**
```bash
ls ~/CLAUDECODE/tools/
# add_fin3_client.sh, add_fin4_client.sh и т.д.
```

**2. Использовать скрипт (Fin3):**
```bash
NEW_UUID=$(python3 -c "import uuid; print(uuid.uuid4())")
bash ~/CLAUDECODE/tools/add_fin3_client.sh <router_name> $NEW_UUID
```

**3. Если скрипта нет — Python с API:**
```python
import uuid, time, json, urllib.request, urllib.parse, http.cookiejar, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def make_session(base):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar)
    )
    data = urllib.parse.urlencode({"username": "ad", "password": "56"}).encode()
    req = urllib.request.Request(f"{base}/login", data=data,
          headers={"Content-Type": "application/x-www-form-urlencoded"})
    with opener.open(req, timeout=15) as r:
        assert json.loads(r.read()).get("success")
    return opener

def add_client(opener, base, ib_id, uid, email):
    ts = int((time.time() + 365*24*3600) * 1000)  # ВСЕГДА так, не хардкодить число!
    payload = json.dumps({
        "id": ib_id,
        "settings": json.dumps({"clients": [{
            "id": uid, "flow": "xtls-rprx-vision", "email": email,
            "limitIp": 0, "totalGB": 1099511627776,
            "expiryTime": ts, "enable": True
        }]})
    }).encode()
    req = urllib.request.Request(f"{base}/panel/api/inbounds/addClient", data=payload,
          headers={"Content-Type": "application/json"})
    with opener.open(req, timeout=15) as r:
        return json.loads(r.read())
```

**4. После addClient — kill xray на сервере:**
```bash
# Fin4:
sshpass -p 'duqwgjXiT4FRrc' ssh root@45.155.55.198 "kill -9 \$(pgrep xray)"
# bMSK:
sshpass -p 'Ujkjdf56#' ssh root@159.194.198.172 "kill -9 \$(pgrep xray)"
# Fin3:
sshpass -p 'Ujkjdf56' ssh root@144.31.66.115 "kill -9 \$(pgrep xray)"
```

**5. Проверить UUID в конфиге:**
```bash
sshpass -p 'duqwgjXiT4FRrc' ssh root@45.155.55.198 \
  "grep -c 'NEW_UUID_PART' /usr/local/x-ui/bin/config.json"
# Должно быть > 0. Если 0 → снова kill -9 $(pgrep xray)
```

**6. КРИТИЧНО для Fin4 — проверить на каком inbound зарегистрирован UUID:**
```bash
sshpass -p 'duqwgjXiT4FRrc' ssh root@45.155.55.198 python3 - << 'EOF'
import json
with open('/usr/local/x-ui/bin/config.json') as f: c = json.load(f)
for ib in c.get('inbounds', []):
    s = ib.get('settings', {})
    if isinstance(s, str): s = json.loads(s)
    for cl in s.get('clients', []):
        if 'UUID_FRAGMENT' in cl.get('id', ''):
            print(f'port={ib["port"]} email={cl["email"]}')
EOF
# port=4191 → использовать bMSK:5223, sid=4b929012
# port=4192 → использовать bMSK:5228, sid=ae2bfb99
```

**7. check_vless.py → должен быть READY ✓✓✓:**
```bash
echo 'vless://...' | python3 ~/CLAUDECODE/check_vless.py -
# Все 5 зелёных: ● TCP ● TLS ● xray ● expiry ● limit
# Только ● READY ✓✓✓ допускает установку на роутер
```

### ❌ Ошибки при создании ключей:
- `expiryTime` из хардкодного числа — только `int((time.time()+365*24*3600)*1000)`
- `limitIp > 0` — всегда 0
- `flow="xtls-rprx-vision"` для gRPC inbound — только `flow=""`
- Считать ключ рабочим "потому что только что создан" — без check_vless READY не ставить

---

## Шаг 4 — Конфигурация podkop

### Стандартный шаблон (Москва, bMSK схема):

```bash
# Main профиль
uci set podkop.main=service
uci set podkop.main.enabled='1'
uci set podkop.main.proxy_string='vless://UUID@159.194.198.172:5223?security=reality&sni=www.microsoft.com&fp=chrome&pbk=ПОЛНЫЙ_PBK&sid=4b929012&type=tcp&flow=xtls-rprx-vision#router-main'
uci set podkop.main.dns_type='udp'            # ТОЛЬКО udp или doh. НИКОГДА fakeip!
uci set podkop.main.dns_server='1.1.1.1'
uci set podkop.main.bootstrap_dns_server='1.1.1.1'

# Community lists (telegram и meta — ВСЕГДА первые!)
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

# YT профиль
uci set podkop.YT=service
uci set podkop.YT.enabled='1'
uci set podkop.YT.proxy_string='vless://UUID@159.194.198.172:8853?security=reality&...'
uci set podkop.YT.dns_type='udp'
uci set podkop.YT.dns_server='1.1.1.1'
uci set podkop.YT.bootstrap_dns_server='1.1.1.1'
uci add_list podkop.YT.community_lists='youtube'

# Глобальные настройки
uci set podkop.settings.exclude_ntp='1'       # ОБЯЗАТЕЛЬНО для всех роутеров!
uci set podkop.settings.download_lists_via_proxy='1'  # если GitHub заблокирован ISP

uci commit podkop
/etc/init.d/podkop enable
/etc/init.d/podkop start
```

### Профиль Calls:
- **Удалять** при обнаружении. Только main и YT.

### ❌ Не трогать dnsmasq вручную:
Podkop сам управляет dnsmasq при старте/стопе.
`uci set dhcp.@dnsmasq[0].noresolv=1` и т.п. — НЕ ДЕЛАТЬ.

---

## Шаг 5 — Тестирование

### Проверка DNS и трафика:

```bash
# FakeIP должен выдавать 198.18.x.x для заблокированных сайтов
nslookup telegram.org 127.0.0.1     # → 198.18.x.x
nslookup youtube.com 127.0.0.1      # → 198.18.x.x
nslookup google.com 127.0.0.1       # → обычный IP (не заблокирован)

# HTTP тесты (301/302 = OK)
curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://telegram.org    # 302
curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://youtube.com     # 301
curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://facebook.com    # 301
curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://tiktok.com      # 301
```

**Если DNS возвращает 198.18.x.x, но HTTP даёт 000:**
→ sing-box не может достучаться до relay. Проверь порт relay и соответствие UUID/inbound (Шаг 3, пункт 6).

**Если LuCI показывает красный профиль, но curl работает:**
→ LuCI health check у sing-box-tiny не работает. Не паниковать. Проверить curl тестами.

---

## Шаг 6 — Проверка перед ребутом (5 обязательных пунктов)

```bash
uci get tailscale.settings.fw_mode                                          # → none
/etc/init.d/tailscale enabled 2>&1 | grep -q "enabled" && echo ENA || echo DIS  # → DIS
grep -q tailscaled /etc/rc.local && echo OK || echo MISSING                # → OK
crontab -l | grep -q watchdog && echo OK || echo MISSING                   # → OK
uci get podkop.settings.exclude_ntp                                        # → 1
```

**Хотя бы один ❌ → сначала починить, только потом запрашивать ребут.**

### Формат запроса ребута (обязательный):

```
🔁 Запрос на перезагрузку: [имя роутера / IP]

Причина: [зачем]

✅ fw_mode = none
✅ init.d DISABLED
✅ rc.local присутствует (tailscaled запустится)
✅ watchdog в crontab
✅ exclude_ntp = 1

Риски: [что может пойти не так]

Разрешаешь?
```

**Ребут молча — ЗАПРЕЩЁН.**

---

## Особые случаи

### ISP блокирует GitHub (install.sh не работает)

```bash
# 1. Проверить блокировку:
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://github.com
# 000 = заблокировано

# 2. Не тратить время на proxy/wrapper! Сразу передавать пакеты с Mac:
cat ~/CLAUDECODE/openwrt-packages/sing-box-tiny_*.ipk | \
    sshpass -p '56756789' ssh root@ROUTER_IP 'cat > /tmp/sing-box-tiny.ipk'
cat ~/CLAUDECODE/openwrt-packages/podkop-*.ipk | \
    sshpass -p '56756789' ssh root@ROUTER_IP 'cat > /tmp/podkop.ipk'
cat ~/CLAUDECODE/openwrt-packages/luci-app-podkop-*.ipk | \
    sshpass -p '56756789' ssh root@ROUTER_IP 'cat > /tmp/luci-app-podkop.ipk'

# 3. Установка на роутере (opkg может игнорировать локальный файл → извлекать вручную):
opkg install --nodeps /tmp/sing-box-tiny.ipk
tar -xzOf /tmp/podkop.ipk ./data.tar.gz | tar -xz -C /
tar -xzOf /tmp/luci-app-podkop.ipk ./data.tar.gz | tar -xz -C /

# 4. После старта с зелёными ключами — включить загрузку через прокси:
uci set podkop.settings.download_lists_via_proxy=1
uci commit podkop
/etc/init.d/podkop restart
```

### Нет места на overlay (< 5MB)

```bash
# Проверить
df -h | grep overlay

# Найти что занимает место
du -sh /overlay/upper/*

# Типичные виновники:
# /overlay/upper/.cache/tailscale-update/ — обновления tailscale
ls -lh /overlay/upper/.cache/tailscale-update/
rm -rf /overlay/upper/.cache/tailscale-update/
# После удаления: отключить автообновление
uci set tailscale.settings.autoupdate='false'
uci commit tailscale

# Если всё равно мало — использовать sing-box-tiny (10MB вместо 39MB):
# ~/CLAUDECODE/openwrt-packages/sing-box-tiny_*.ipk
```

### Tailscale перезаписывает /etc/resolv.conf

```bash
# Симптом: DNS через 100.100.100.100 вместо dnsmasq → podkop не работает
cat /etc/resolv.conf  # → nameserver 100.100.100.100 = проблема

# Исправить:
ln -sf /tmp/resolv.conf /etc/resolv.conf 2>/dev/null || \
ln -sf /var/run/dnsmasq/resolv.conf /etc/resolv.conf 2>/dev/null

# Добавить защиту в ts-watchdog.sh (см. Шаг 1)
```

### Xiaomi AX3000T (apk вместо opkg)

```bash
# На AX3000T используется apk (Alpine Package Keeper), не opkg
apk add tailscale    # вместо opkg install tailscale
apk info | grep tailscale  # проверка установленных

# userspace-networking обязателен (как всегда)
# init.d DISABLED (как всегда)
# WiFi: два уровня disabled (radio + iface)
```

### Установка podkop через itdog скрипт (рабочий метод)

**Применяется:** OpenWrt 24.10.x (opkg) и 25.12 (apk). Скрипт сам определяет менеджер пакетов.

**Шаг 1 — Скачать скрипт:**
```bash
wget -qO /tmp/install.sh https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh
```

**Шаг 2 — Запустить с автоответом (y = выбрать русский язык):**
```bash
sh /tmp/install.sh << INPUT
y
INPUT
```

Скрипт автоматически: обновляет opkg/apk, скачивает podkop + luci-app-podkop + русификацию + полный sing-box, устанавливает всё.

**⚠️ ВАЖНО после установки — удалить russia_inside:**
```bash
# itdog АВТОМАТИЧЕСКИ добавляет russia_inside в community_lists
# Это лишнее — удалить сразу после установки
uci del_list podkop.settings.community_lists='russia_inside' 2>/dev/null
# Также проверить что telegram и meta стоят ПЕРВЫМИ:
uci get podkop.settings.community_lists
```

**❌ Что НЕ работает (проверено 06.05.2026):**
- `yes y | sh <(wget -O - URL)` — зависает (yes пишет бесконечно, блокирует скрипт)
- `printf 'y\n' | sh <(...)` — тоже зависает при process substitution
- `cat ipk | opkg install --nodeps` с all.ipk — ошибка "incompatible with architectures configured"
- `opkg install --nodeps --force-architecture` — не помогает для all.ipk

**Для 25.12 (apk роутеры):** тот же скрипт, скачивается так же. Скрипт сам использует `apk add`.

---

## Топ-10 ошибок (из реальных сессий)

### 1. Красный ключ — диагностировать sing-box
**Правило:** красный = сразу новый ключ. Не смотреть логи, не проверять nft.

### 2. UUID на Fin4:4192, но ключ через bMSK:5223
**Правило:** После addClient → SSH на Fin4 → проверить на каком порту UUID. 4191→5223, 4192→5228.

### 3. dns_type='fakeip'
**Правило:** fakeip — внутренний механизм podkop, не тип DNS. Только `udp` или `doh`.

### 4. Трогать dnsmasq вручную
**Правило:** podkop сам управляет dnsmasq. Не делать `uci set dhcp.@dnsmasq[0].*`.

### 5. Запускать ITDog install.sh при заблокированном GitHub
**Правило:** сначала проверить `curl https://github.com`. 000 → передавать пакеты с Mac.

### 6. tailscale serve в rc.local
**Правило:** НИКОГДА не добавлять `tailscale serve` — заблокирует SSH навсегда.

### 7. --state= вместо --statedir=
**Правило:** только `--statedir=/etc/tailscale/`. `--state=` ломает авторизацию после ребута.

### 8. expiryTime из хардкодного числа
**Правило:** только `int((time.time()+365*24*3600)*1000)`. Никогда не копировать числа.

### 9. Начинать с podkop, не обеспечив Tailscale-устойчивость
**Правило:** Tailscale watchdog+rc.local+fw_mode — ДО любого ремонта podkop.

### 10. Не проверять релей перед заменой ключа
**Правило:** `uci get podkop.main.proxy_string` — посмотреть на какой адрес идёт ключ, потом менять.

### 11. itdog скрипт добавляет russia_inside — не забыть удалить
**Правило:** после установки через itdog install.sh сразу проверить `uci get podkop.settings.community_lists`. Если есть `russia_inside` — удалить: `uci del_list podkop.settings.community_lists='russia_inside'`. Оставить только нужные списки с telegram и meta первыми.

---

## Справочник паролей SSH (быстрый доступ)

| Устройство | IP | Пароль |
|---|---|---|
| Все роутеры | любой | `56756789` |
| Fin3 | 144.31.66.115 | `Ujkjdf56` |
| Fin4 | 45.155.55.198 | `duqwgjXiT4FRrc` |
| bMSK | 159.194.198.172 | `Ujkjdf56#` |
| bSPB | 5.35.84.151 | SSH закрыт — только панель |
| PL4 | 82.38.66.75 | `T-RUeIl9%+` |
| X-UI панели | все | login: `ad` / password: `56` |

Полные данные: `~/CLAUDECODE/MASTER_CREDENTIALS.md`

---

## Checklist финальный (перед закрытием задачи)

```
[ ] Tailscale: fw_mode=none, init.d DISABLED, rc.local OK, watchdog OK
[ ] exclude_ntp = 1
[ ] Оба профиля (main + YT) зелёные или проверены curl-тестами
[ ] community_lists: telegram и meta первые, минимум 20 списков
[ ] DNS: dns_server=1.1.1.1, bootstrap_dns_server=1.1.1.1
[ ] curl тесты: TG=302, YT=301, FB=301
[ ] Если был ребут — все пункты выше подтверждены после ребута
[ ] UUID роутера записан в xui_inbounds_registry.md
```

---

*Создано: 2026-05-02 | Обновлять после каждой новой ошибки или нового паттерна*
