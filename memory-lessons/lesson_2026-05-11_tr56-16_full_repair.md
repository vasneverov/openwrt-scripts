# Урок: tr56-16 — полный ремонт + fw4-fix + Tailscale watchdog

**Дата:** 2026-05-11 (ночь)
**Роутер:** Cudy TR3000 v1 (tr56-16)
**IP:** 192.168.5.1 → Tailscale 100.68.181.47
**Провайдер:** 56-й дом (через eth0, шлюз 192.168.7.1)

---

## 1. Что сделано

### 1.1 Диагностика
- PodkopTable есть, 13 sets, 4 rules
- sing-box работает (PID 31122, 1271M)
- **Проблема:** `reality verification failed` — pbk не совпадал с PL5
- **Решение:** пользователь сам поставил правильный ключ

### 1.2 fw4-fix (критично!)
- Установлен скрипт `podkop-fw4-fix.sh` с репозитория vasneverov/openwrt-scripts
- Применён `install` и `update`
- **Без fw4-fix после ребута PodkopTable не создаётся** — прокси не работает

### 1.3 Tailscale
- fw_mode=none (не лезет в iptables)
- init.d DISABLED (запуск через rc.local)
- rc.local: tailscaled → tailscale up --reset (сброс старых флагов)
- ts-watchdog v3.1: lock-файл, NoState fix, не убивает если онлайн
- **serve anchor НЕ НУЖЕН** — watchdog держит соединение

### 1.4 Watchdog-ы (каждые 2 мин)
- `ts-watchdog.sh` — Tailscale (NoState fix + lock-файл)
- `podkop-watchdog.sh` — sing-box процесс
- `route-watchdog.sh` — PodkopTable nft таблица
- `podkop list_update` — каждые 3 часа

### 1.5 Ребут
- Прокси поднялся на +60s
- Tailscale поднялся на +125s
- После ребута всё работает

---

## 2. Проблемы и решения

### 2.1 reality verification failed
**Симптом:** sing-box ERROR: `connection download closed: reality verification failed`
**Причина:** pbk в proxy_string не совпадает с privateKey на сервере
**Решение:** поставить правильный pbk (вычисляется из privateKey сервера)

### 2.2 Podkop не стартует после ребута
**Симптом:** podkop status = "not running", PodkopTable есть но правила не работают
**Причина:** fw4 не применяет правила PodkopTable после перезагрузки
**Решение:** `podkop-fw4-fix.sh install` — добавляет хук в /etc/nftables.d/

### 2.3 Tailscale не поднимается после ребута
**Симптом:** tailscale status пустой, tailscaled запущен но не онлайн
**Причина:** tailscale up без --reset не сбрасывает старые advertise-routes
**Решение:** `tailscale up --reset --accept-dns=false --accept-routes`

### 2.4 DNS не работает (ping: bad address)
**Симптом:** ping google.com → "bad address", но nslookup работает
**Причина:** curl/wget используют системный резолвер, который идёт через 127.0.0.1:53
**Решение:** это нормально для tproxy — curl с роутера не проходит через tproxy. LAN-клиенты работают.

---

## 3. Установка Podkop (install.sh с itdog)

### 3.1 Интерактивные вопросы в install.sh
Скрипт `https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh` задаёт **3 вопроса**:

| Строка | Вопрос | Ожидаемый ответ | Как передать |
|--------|--------|-----------------|--------------|
| 86 | "Continue? (yes/no)" — при обновлении старой версии | `y` | `printf 'y\n...'` |
| 192 | "Русский язык интерфейса ставим? y/n" | `y` (обязательно!) | `printf '...\ny\n...'` |
| 276 | "Conflicting package detected: https-dns-proxy. Remove?" | `y` | `printf '...\ny\n'` |

**Формула для неинтерактивной установки:**
```bash
printf 'y\ny\ny\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh)
```
Где:
- 1-й `y` — подтверждение обновления (если старая версия)
- 2-й `y` — удалить https-dns-proxy (если есть)
- 3-й `y` — русский язык интерфейса (обязательно!)

**Важно:** `printf` передаёт ответы в том порядке, в котором скрипт их запрашивает. Если какого-то вопроса нет (например, нет старой версии) — ответ игнорируется.

### 3.2 Зависимости
- sing-box >= 1.12.4 (если старая — удаляет и ставит новую)
- 15MB свободного места на overlay
- DNS должен работать (nslookup google.com)

---

## 4. Установка Tailscale (install_en.sh с GuNanOvO)

### 4.1 Скрипт
```bash
wget -O /tmp/ts.sh https://raw.githubusercontent.com/GuNanOvO/openwrt-tailscale/main/install_en.sh
chmod +x /tmp/ts.sh
printf '1\n' | /tmp/ts.sh
```

### 4.2 Интерактивные вопросы
Скрипт задаёт **6 вопросов**:

| Строка | Вопрос | Ожидаемый ответ |
|--------|--------|-----------------|
| 438 | "Confirm using persistent installation method?" | `y` (1-й в меню) |
| 273 | "Confirm restart tailscale?" (при обновлении) | `y` |
| 304 | "Confirm uninstall tailscale?" | `n` |
| 373 | "Confirm delete residual files?" | `n` |
| 559 | "Confirm using temporary installation method?" | `n` |
| 997 | "Please enter option (1 ~ N)" — главное меню | `1` (persistent install) |

**Формула для неинтерактивной установки:**
```bash
printf '1\n' | /tmp/ts.sh
```
`1` выбирает первый пункт меню — Persistent Installation.

### 4.3 Флаги
- `--tempinstall` — временная установка (в /tmp, без сохранения после ребута)
- Нет флага `--persistentinstall` — только через меню

### 4.4 После установки
```bash
# Фикс для OpenWrt 25.12
sed -i 's|--statedir=/var/lib/tailscale ||g' /etc/init.d/tailscale
sed -i 's|TS_DEBUG_FIREWALL_MODE="none"|TS_DEBUG_FIREWALL_MODE="$fw_mode"|g' /etc/init.d/tailscale

# Настройка
uci set tailscale.settings.fw_mode='none'
uci set tailscale.settings.state_file='/etc/tailscale/tailscaled.state'
uci set tailscale.settings.autoupdate='false'
uci commit tailscale
mkdir -p /etc/tailscale

# Отключаем init.d (будет через rc.local)
/etc/init.d/tailscale disable
```

---

## 5. Ключевые уроки

### 5.1 fw4-fix — СРАЗУ после podkop
Не откладывать. Без него после ребута прокси не работает. Установка:
```bash
wget -q -O /root/podkop-fw4-fix.sh \
  'https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fw4-fix.sh'
chmod +x /root/podkop-fw4-fix.sh
/root/podkop-fw4-fix.sh install
```

### 5.2 Tailscale — fw_mode=none + init.d DISABLED
- fw_mode=none — tailscale не лезет в iptables/nftables (это делает podkop)
- init.d DISABLED — запуск через rc.local (более надёжно)
- rc.local с `--reset` — сбрасывает старые advertise-routes

### 5.3 Watchdog — lock-файл обязателен
Без lock-файла watchdog из rc.local и watchdog из крона конфликтуют.
Решение: `LOCKFILE=/tmp/ts-watchdog.lock` — проверка PID.

### 5.4 NoState fix
Если tailscale теряет DERP и входит в состояние NoState — нужен полный перезапуск tailscaled:
```bash
killall tailscale 2>/dev/null
sleep 1
killall tailscaled 2>/dev/null
sleep 2
tailscaled --statedir=/etc/tailscale/ --tun=userspace-networking >> /tmp/ts.log 2>&1 &
sleep 5
tailscale up --accept-dns=false --accept-routes &
```

### 5.5 pbk — вычисляется из privateKey
На сервере (xray/x-ui) pbk не хранится в конфиге. Он вычисляется из privateKey.
Команда: `xray x25519 -i <PRIVATE_KEY>`
На PL5 privateKey: `2KiZnuOTLK1y-fzNDtlsbI9WBwRbuoFN1r0cmMQaimM`

---

## 6. Финальный статус tr56-16

```
Podkop:     running ✅
PodkopTable: 13 sets, 4 rules ✅
sing-box:   PID 31122, 1271M ✅
Tailscale:  100.68.181.47, ONLINE ✅
fw_mode:    none ✅
init.d:     DISABLED ✅
exclude_ntp: 1 ✅
enable_output: 1 ✅
WAN:        eth0, gw 192.168.7.1 ✅
Internet:   ping google 23ms, yandex 15ms, github 46ms ✅
DNS:        dig google 216.58.201.14 ✅
Watchdog:   3 шт, каждые 2 мин ✅
fw4-fix:    установлен ✅
check-ip:   установлен ✅
Uptime:     14 мин ✅
Memory:     65% free (322M/497M) ✅
```
