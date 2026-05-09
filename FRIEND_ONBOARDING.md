# 🚀 Полный набор скиллов и тулзов для DeepSeek (Cline)

> Этот файл — полная коллекция всех навыков и инструментов для работы с OpenWrt роутерами, Podkop, Tailscale и VPN.
>
> **Как использовать:** Положи этот файл в `~/CLAUDECODE/` и скажи Cline:
> *"Прочитай FRIEND_ONBOARDING.md и следуй инструкциям"*
>
> DeepSeek сам разберётся, что к чему, и будет использовать все скиллы и тулзы.

---

## 📋 Содержание

1. [Память между сессиями (принципы Карпатого)](#1-память-между-сессиями)
2. [Структура рабочей папки](#2-структура-рабочей-папки)
3. [Железные правила](#3-железные-правила)
4. [Типовой workflow](#4-типовой-workflow)
5. [Типовые проблемы и решения](#5-типовые-проблемы-и-решения)
6. [Модели роутеров](#6-модели-роутеров)
7. [Формат VLESS-ключа](#7-формат-vless-ключа)
8. [Community lists](#8-community-lists)
9. [Полезные команды](#9-полезные-команды)
10. [Скилл: Алгоритм диагностики podkop](#10-скилл-алгоритм-диагностики-podkop)
11. [Скилл: Руководство по ремонту podkop](#11-скилл-руководство-по-ремонту-podkop)
12. [Скилл: Универсальная прошивка роутера](#12-скилл-универсальная-прошивка-роутера)
13. [Скилл: Прошивка Xiaomi AX3000T](#13-скилл-прошивка-xiaomi-ax3000t)
14. [Скилл: Создание ключа-клона](#14-скилл-создание-ключа-клона)
15. [Скилл: Установка podkop](#15-скилл-установка-podkop)
16. [Тулз: Спасительный скрипт (rescue_generic.sh)](#16-тулз-спасительный-скрипт)
17. [Тулз: Фикс блокировки GitHub CDN (podkop-fix-lists.sh)](#17-тулз-фикс-блокировки-github-cdn)
18. [Тулз: Фикс forwarded трафика (podkop-fw4-fix.sh)](#18-тулз-фикс-forwarded-трафика)
19. [Тулз: Создание VLESS ключа (create_vless_key.py)](#19-тулз-создание-vless-ключа)
20. [Тулз: Добавление клиента на Fin3 (add_fin3_client.sh)](#20-тулз-добавление-клиента-на-fin3)
21. [Тулз: Проверка podkop на роутере (check-yt-on-router.sh)](#21-тулз-проверка-podkop-на-роутере)
22. [Тулз: Tmux-бокс (tbox.sh)](#22-тулз-tmux-бокс)
23. [Тулз: Ремонт 3 роутеров (t3.sh)](#23-тулз-ремонт-3-роутеров)

---

## 1. Память между сессиями (принципы Андрея Карпатого)

### 1.1 Главный принцип: память живёт в файлах, не в модели

DeepSeek (как и любая LLM) **не помнит** прошлые сессии.  
Вся память хранится в текстовых файлах в рабочей папке.

**При старте каждой новой сессии Cline должен прочитать:**
1. **`IRON_RULES.md`** — железные правила (нарушение = поломка роутера)
2. **`deepsick_memory.md`** — памятка: что делали, какие решения приняли
3. **`memory-lessons/`** — последний урок (чтобы знать контекст)
4. **`FRIEND_ONBOARDING.md`** — этот файл (структура знаний)

### 1.2 Файловая система памяти

```
~/CLAUDECODE/
├── deepsick_memory.md          # Памятка между сессиями (читать первой!)
├── IRON_RULES.md               # Железные правила
├── memory-lessons/             # Уроки из каждого ремонта
│   └── lesson_*.md             # Каждый урок — отдельный файл
├── skills/                     # Скиллы (навыки для AI)
├── tools/                      # Скрипты для работы
└── .aider.rules                # Правила для aider (DeepSeek CLI)
```

### 1.3 Как работает память

1. **`deepsick_memory.md`** — обновляется в конце каждой сессии:
   - Что сделали
   - Какие решения приняли
   - Какие проблемы нашли
   - Какие задачи на будущее

2. **`memory-lessons/`** — создаётся новый файл после каждого ремонта:
   - Имя: `lesson_ДАТА_ОПИСАНИЕ.md`
   - Содержит: проблему, диагностику, решение, выводы

3. **Правило:** Если что-то починил → напиши урок в `memory-lessons/`

### 1.4 Что должен делать Cline при старте

```markdown
1. Прочитать deepsick_memory.md
2. Прочитать IRON_RULES.md
3. Найти последний файл в memory-lessons/
4. Прочитать FRIEND_ONBOARDING.md
5. Только после этого начинать работу
```

### 1.5 Что должен делать Cline в конце сессии

```markdown
1. Обновить deepsick_memory.md (добавить что сделали)
2. Создать урок в memory-lessons/ (если был ремонт)
3. Закоммитить изменения в git
```

---

## 2. Структура рабочей папки

```
~/CLAUDECODE/
├── IRON_RULES.md                    # Железные правила — читать ПЕРВЫМ
├── ROUTER_FLASH_AND_DIAG_GUIDE.md   # Прошивка роутеров — полный гайд
├── ROUTER_REPAIR_GUIDE.md           # Ремонт роутеров — справочник ошибок
├── ROUTER_DIAG_PROTOCOL.md          # Протокол диагностики — пошагово
├── INFRASTRUCTURE_ARCHITECTURE.md   # Архитектура VPN
├── FRIEND_ONBOARDING.md             # ← Этот файл
├── deepsick_memory.md               # Памятка между сессиями
│
├── tools/                           # Скрипты для работы
│   ├── rescue_generic.sh            # Спасительный скрипт для роутера
│   ├── podkop-fix-lists.sh          # Чинит блокировку GitHub CDN
│   ├── podkop-fw4-fix.sh            # Чинит forwarded трафик
│   ├── add_fin3_client.sh           # Добавление клиента на Fin3
│   ├── create_vless_key.py          # Создание VLESS-ключа
│   ├── check-yt-on-router.sh        # Проверка podkop на роутере
│   ├── port_scanner.py              # Сканер портов
│   ├── tbox.sh                      # Tmux-бокс для работы
│   └── t3.sh                        # Ремонт 3 роутеров параллельно
│
├── skills/                          # Скиллы (навыки для AI)
│   ├── podkop_diag_algo.md          # Алгоритм диагностики podkop
│   ├── podkop_repair_guide.md       # Памятка по ремонту podkop
│   ├── flash_router_universal.md    # Универсальная прошивка
│   ├── flash_xiaomi_ax3000t.md      # Прошивка Xiaomi AX3000T
│   ├── podkop_install_guide.md      # Установка podkop
│   └── create_clone_key.md          # Создание клон-ключа
│
├── memory-lessons/                  # Уроки из реальных ремонтов
│   └── lesson_*.md                  # Каждый урок — отдельный файл
│
├── openwrt-packages/                # Пакеты для OpenWrt 24.x (opkg)
├── openwrt-apk-packages/            # Пакеты для OpenWrt 25.12 (apk)
├── openwrt-lists/                   # Списки community_lists
│
├── ключи/                           # VLESS-ключи роутеров
├── servers/                         # Конфиги серверов
│
├── check_vless.py                   # Проверка VLESS-ключей
├── vless_key.py                     # Генерация VLESS-ключей
├── flash-router.sh                  # Скрипт прошивки
└── tmux-router-repair.sh            # Сессия tmux для ремонта
```

---

## 3. Железные правила

### 3.1 Tailscale — НЕ ТРОГАТЬ
- **Никогда** не перезапускать tailscaled
- **Никогда** не менять `tailscale up` (даже `--reset`)
- **Никогда** не перезагружать firewall (fw4) — это сносит nftables и Tailscale отваливается
- **Никогда** не применять `nft flush` — это убивает Tailscale
- `fw_mode` должен быть **всегда `none`**
- `init.d tailscale` должен быть **всегда DISABLED**
- `rc.local` должен содержать запуск `tailscaled --tun=userspace-networking`
- Watchdog в crontab — **обязательно** (каждые 2-3 минуты)
- `exclude_ntp = 1` — **обязательно**
- `autoupdate = false` — **обязательно**

### 3.2 Podkop — НЕ ПЕРЕЗАПУСКАТЬ вручную
- Только через watchdog или `list_update`
- Если нужно применить изменения — перезагрузить роутер целиком
- **Никогда** не использовать `dns_type='fakeip'` — только `udp` или `doh`
- **Никогда** не трогать dnsmasq вручную — podkop сам управляет
- **Никогда** не создавать профиль `calls` — только `main` и `YT`

### 3.3 Перед любыми изменениями — сохранять бэкап
- `/etc/config/network`
- `/etc/config/podkop`
- `/etc/config/tailscale`
- `/etc/rc.local`

### 3.4 Если роутер пропал — не паниковать
- Подождать 2 минуты (watchdog)
- Если не появился — просить перезагрузить питание
- После появления — сразу зайти и проверить

### 3.5 check-ip — обязательная проверка после любого ремонта
- Через прокси (как LAN-клиент) — должен быть зарубежный IP
- Напрямую (с роутера) — должен быть российский IP
- Все основные сайты должны быть доступны

### 3.6 Перед ребутом — 5 обязательных проверок
1. `fw_mode = none` ✅
2. `init.d tailscale DISABLED` ✅
3. `rc.local` содержит tailscaled ✅
4. Watchdog в crontab ✅
5. `exclude_ntp = 1` ✅

**Хотя бы один ❌ → сначала починить, потом ребутить.**

### 3.7 Ключи — проверять перед установкой
- `python3 ~/CLAUDECODE/check_vless.py <ключ>`
- Только если `● READY ✓✓✓` — ставить на роутер
- Ключи для нового роутера — брать с работающего (менять только UUID)

### 3.8 Все действия — логировать
- Каждый шаг — в вывод
- Каждый урок — в `memory-lessons/`
- Каждое изменение — коммитить в git

---

## 4. Типовой workflow

### 4.1 Прошивка нового роутера
```
1. Определить модель и год (спросить пользователя)
2. Выбрать правильную прошивку
3. Залить прошивку (SCP или stdin pipe)
4. Дождаться возврата (30-45 сек)
5. Накатить шаблон (или настроить вручную)
6. Установить Podkop (через itdog install.sh или локальные пакеты)
7. Настроить Podkop (main + YT профили)
8. Установить Tailscale (gunanovo APK или apk add)
9. Настроить Tailscale (fw_mode=none, init.d DISABLED, rc.local, watchdog)
10. Авторизовать Tailscale
11. 5-пунктовая проверка перед ребутом
12. Ребут и мониторинг
13. Финальная проверка
```

### 4.2 Ремонт роутера
```
1. Собрать информацию (диагностика)
2. Проверить Tailscale-устойчивость (Шаг 1)
3. Диагностировать Podkop (Шаг 2)
4. Если ключ красный — создать новый (Шаг 3)
5. Настроить Podkop (Шаг 4)
6. Протестировать (Шаг 5)
7. Проверить перед ребутом (Шаг 6)
8. Финальная проверка
```

### 4.3 Диагностика (8 компонентов)
```
1. Система (hostname, версия OpenWrt)
2. Tailscale (статус, fw_mode, init.d, rc.local, watchdog)
3. Podkop (sing-box, exclude_ntp, DNS)
4. Сеть (carrier, default route)
5. Ключи (main proxy_string)
6. Тесты (Google, YouTube, Telegram)
7. Дисковое место (overlay)
8. Логи ошибок
```

---

## 5. Типовые проблемы и решения

### Проблема: Telegram/Meta не работают
**Причина:** Неправильные community_lists или неверный relay адрес.
**Решение:** Проверить что telegram и meta — ПЕРВЫЕ в списке. Проверить relay адрес.

### Проблема: YouTube не работает
**Причина:** YT профиль не настроен или неправильный ключ.
**Решение:** Проверить YT профиль. Если не работает — удалить YT, добавить youtube в main.

### Проблема: sing-box не запускается
**Причина:** Race condition или нет места на overlay.
**Решение:** `/etc/init.d/podkop restart`, подождать 8 сек. Если overlay full — удалить `.cache/tailscale-update/`.

### Проблема: Tailscale серая точка
**Причина:** tailscaled не запущен или rc.local повреждён.
**Решение:** Проверить процесс, восстановить rc.local из rc.local.bak, запустить вручную.

### Проблема: GitHub заблокирован
**Причина:** Провайдер блокирует Fastly CDN.
**Решение:** Копировать пакеты с компа через `cat | ssh` pipe. Установить `podkop-fix-lists.sh`.

### Проблема: Нет места на overlay
**Причина:** tailscale-update кэш или логи.
**Решение:** `rm -rf /overlay/upper/.cache/tailscale-update/`. Использовать sing-box-tiny (10MB вместо 39MB).

---

## 6. Модели роутеров

| Модель | Прошивка | SCP метод | Пакетный менеджер |
|--------|----------|-----------|-------------------|
| Cudy WR3000H v1 | `*-wr3000h-v1-sysupgrade.bin` | scp -O | apk |
| Cudy TR3000 v1 | `*-tr3000-v1-sysupgrade.bin` | scp -O | apk |
| Cudy M3000 v1 (24год) | `*-m3000-v1-sysupgrade.bin` | **stdin pipe** | apk |
| Cudy M3000 v2 (25год) | то же + **`-F`** | **stdin pipe** | apk |
| Cudy WR3000S v1 | `*-wr3000s-v1-sysupgrade.bin` | scp -O | apk / opkg |
| Xiaomi AX3000T | `*-ax3000t-sysupgrade.bin` | scp -O | apk |

**Factory IP:** `192.168.1.1`, пароль пустой
**После шаблона:** `192.168.5.1`, пароль `56756789`

---

## 7. Формат VLESS-ключа

```
vless://UUID@HOST:PORT?type=grpc&security=reality&mode=gun&serviceName=&pbk=PBK&sid=SID&sni=www.apple.com&fp=chrome&spx=%2F#LABEL
```

**Обязательно:**
- `type=grpc` (НЕ tcp)
- `fp=chrome`
- `sni=www.apple.com`
- Нет `/` перед `?`

---

## 8. Community lists

Порядок для Main (telegram и meta — ВСЕГДА ПЕРВЫМИ):
```
telegram, meta, geoblock, block, porn, news, anime, discord, twitter,
hdrezka, tiktok, cloudflare, google_ai, google_play, hodca, roblox,
hetzner, ovh, digitalocean, cloudfront
```

---

## 9. Полезные команды

### Проверка ключа
```bash
echo 'vless://...' | python3 ~/CLAUDECODE/check_vless.py -
```

### Диагностика роутера (одним SSH)
```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@100.x.x.x "
echo '=== 1. СИСТЕМА ===' && hostname && grep DISTRIB_RELEASE /etc/openwrt_release
echo '=== 2. TAILSCALE ===' && tailscale status 2>&1 | head -3
echo '=== 3. PODKOP ===' && ps | grep sing-box | grep -v grep || echo 'sing-box не запущен'
echo '=== 4. ТЕСТЫ ===' && curl -s -o /dev/null -w 'Google: %{http_code}\n' --connect-timeout 5 https://www.google.com
curl -s -o /dev/null -w 'YouTube: %{http_code}\n' --connect-timeout 5 https://www.youtube.com"
```

### 5-пунктовая проверка перед ребутом
```bash
sshpass -p '56756789' ssh root@100.x.x.x "
echo '1.' && /etc/init.d/tailscale enabled && echo 'FAIL:ENABLED' || echo 'OK:DISABLED'
echo '2.' && uci get tailscale.settings.fw_mode
echo '3.' && grep -q tailscaled /etc/rc.local && echo 'OK:rc.local' || echo 'FAIL:rc.local'
echo '4.' && crontab -l | grep ts-watchdog && echo '(watchdog OK)' || echo 'FAIL:watchdog'
echo '5.' && uci get podkop.settings.exclude_ntp"
```

---

## 10. Скилл: Алгоритм диагностики podkop

> **Цель:** Универсальный алгоритм, по которому любая модель (Claude, GPT, DeepSeek и т.д.) может диагностировать и чинить podkop на OpenWrt роутере.

### 10.1 Быстрая проверка (1 минута)

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

### 10.2 Если листы не обновляются

**Симптом:** В логах podkop:
```
[warn] Attempt 1/3 to download http://127.0.0.1/Subnets/IPv4/telegram.lst failed
```

**Причина:** Провайдер блокирует `raw.githubusercontent.com`.

**Диагностика:**
```bash
nslookup raw.githubusercontent.com
ping -c 2 185.199.108.133
curl -sL -o /dev/null -w "HTTP %{http_code} Time: %{time_total}s\n" \
  --max-time 10 "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Subnets/IPv4/meta.lst"
```

**Лечение:** Установить `podkop-fix-lists.sh` (см. тулз №17).

### 10.3 Если sing-box не запускается

**Симптом:** `pgrep -a sing-box` ничего не показывает.

**Диагностика:**
```bash
logread -e sing-box | tail -20
sing-box check -c /etc/sing-box/config.json 2>&1
uci get podkop.main.mixed_proxy_enabled
```

**Лечение:**
```bash
# Если mixed_proxy_enabled=1 — выключить
uci set podkop.main.mixed_proxy_enabled=0
uci commit podkop
/etc/init.d/podkop reload
```

### 10.4 Если клиентские устройства не работают

**Симптом:** С роутера всё пингуется, но клиенты (WiFi/LAN) не выходят в интернет.

**Диагностика:**
```bash
# Проверить DNS на клиентах (должен быть 192.168.1.1)
# Проверить NAT/masquerade
iptables -t nat -L -n 2>/dev/null | grep MASQUERADE
# Проверить DHCP
cat /tmp/dhcp.leases
```

### 10.5 Диагностика forwarded трафика (OpenWrt 25.12+)

**Главный вопрос:** Видит ли podkop трафик от клиентов (ноутбуки, телефоны) или только с самого роутера?

На OpenWrt 25.12+ (fw4/nftables) таблица `inet PodkopTable` с `hook prerouting` **может не видеть forwarded трафик** (с клиентов WiFi/LAN).

**Диагностика:**
```bash
# 1. Проверить счётчики PodkopTable mangle (prerouting)
nft list chain inet PodkopTable mangle 2>/dev/null | grep "counter" | head -5

# 2. Проверить счётчики fw4 mangle_forward
nft list chain inet fw4 mangle_forward 2>/dev/null | grep "counter" | head -5

# 3. Проверить счётчики TPROXY
nft list chain inet PodkopTable proxy 2>/dev/null | grep "counter"
```

**Интерпретация:**
| Ситуация | PodkopTable mangle | fw4 mangle_forward | Вывод |
|---|---|---|---|
| ✅ Всё работает | packets > 0 | packets > 0 | Всё ок |
| ⚠️ Только local | packets > 0 | packets = 0 | **Нужен podkop-fw4-fix** |
| ❌ Ничего не работает | packets = 0 | packets = 0 | Проблема не в forwarded |

**Решение:** Установить `podkop-fw4-fix.sh` (см. тулз №18).

### 10.6 WAN ifname — частая причина неработающего podkop

**Симптом:** Podkop запущен, сайты работают, но `check-ip` показывает российский IP.

**Причина:** Podkop использует `uci get network.wan.ifname` для определения WAN-интерфейса. Если в конфиге сети указан `device` вместо `ifname` — podkop не видит WAN.

**Диагностика:**
```bash
uci get network.wan.ifname
# Если пусто — проблема!
ip route show table podkop
# Должно быть: default via GATEWAY dev IFACE
# Если: local default dev lo scope host — проблема!
```

**Лечение:**
```bash
uci set network.wan.ifname='eth0'  # заменить на актуальный интерфейс
uci commit network
/etc/init.d/podkop restart
```

### 10.7 Community lists — проверка и обновление

**Симптом:** Podkop запущен, но `check-ip` показывает российский IP. Счётчики nftables `@podkop_subnets` = 0.

**Диагностика:**
```bash
find /etc/podkop/ -type f
uci get podkop.settings.download_community_lists_via_proxy
uci get podkop.settings.download_lists_via_proxy
```

**Лечение:**
```bash
uci set podkop.settings.download_community_lists_via_proxy='0'
uci set podkop.settings.download_lists_via_proxy='0'
uci commit podkop
podkop list_update
/etc/init.d/podkop restart
```

### 10.8 Правильный check-ip скрипт

```bash
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

### 10.9 Чеклист для прошивки/ремонта

```bash
# 1. Подключиться по Tailscale
# 2. Быстрая проверка
# 3. Если роутер нестабилен — спасительный скрипт
# 4. Если листы не обновляются — листовой скрипт
# 5. Если sing-box не стартует — проверить mixed_proxy
# 6. ФИНАЛЬНАЯ ПРОВЕРКА: проверить IP с роутера И с клиента
# 7. Если с клиента не работает — fw4-fix скрипт
# 8. Сохранить урок в memory-lessons/
```

---

## 11. Скилл: Руководство по ремонту podkop

### 11.1 Почему podkop перестал работать "из коробки"

OpenWrt 25.12 перешёл с `fw3`/`iptables` на `fw4`/`nftables`.  
В новой системе `inet` таблицы с `hook prerouting` **не видят forwarded трафик** (с клиентов).

- **OpenWrt < 25.12** (23.05, 24.10): `fw3` + `iptables` → `mangle PREROUTING` видел ВЕСЬ трафик
- **OpenWrt 25.12**: `fw4` + `nftables` → `inet PodkopTable prerouting` видит **только local** трафик
- **Решение:** Добавлять правила в `inet fw4 mangle_forward` (hook forward) — он видит forwarded трафик

### 11.2 Быстрая диагностика

```bash
# 1. Статус podkop
/etc/init.d/podkop status

# 2. Статус sing-box
/etc/init.d/sing-box status

# 3. Проверка IP (должен показывать не Россию)
curl -s https://2ip.ru | head -3
curl -s https://myip.ipip.net

# 4. Проверка nftables (счётчики должны быть > 0)
nft list chain inet PodkopTable mangle 2>/dev/null | head -10

# 5. Проверка mangle_forward (должны быть podkop-fw4-fix правила)
nft list chain inet fw4 mangle_forward 2>/dev/null | grep "podkop-fw4-fix"
```

### 11.3 Если podkop не работает

```bash
# 1. Перезапустить podkop
/etc/init.d/podkop restart

# 2. Подождать 30-40 секунд пока загрузятся списки
sleep 40

# 3. Обновить fw4-fix (если установлен)
/root/podkop-fw4-fix.sh update

# 4. Проверить
curl -s https://2ip.ru | head -3
```

### 11.4 Важные моменты

1. **`podkop status` показывает `not running`** — это НОРМАЛЬНО для OpenWrt 25.12. Podkop — не демон, а одноразовый скрипт.
2. **После перезагрузки роутера** podkop запускается автоматически через `/etc/rc.d/S99podkop`.
3. **Проверять работу нужно с клиента** (ноутбук/телефон за роутером), а не с самого роутера через SSH.
4. **enable_output_network_interface=1** — чтобы трафик с самого роутера тоже шёл через прокси.

---

## 12. Скилл: Универсальная прошивка роутера

### 12.1 Таблица роутеров

| Модель | Кодовое имя | Архитектура | Flash | Sing-box | Tailscale |
|--------|-------------|-------------|-------|----------|-----------|
| Xiaomi AX3000T | `xiaomi_mi-router-ax3000t` | aarch64_cortex-a53 | 128MB | толстый | толстый |
| Cudy M3000 v1/v2 | `cudy_m3000-v1` | aarch64_cortex-a53 | 128MB | толстый | толстый |
| Cudy WR3000H v1 | `cudy_wr3000h-v1` | aarch64_cortex-a53 | 128MB | толстый | UPX |
| Cudy WR3000S v1 | `cudy_wr3000s-v1` | aarch64_cortex-a53 | 128MB | толстый | UPX |
| Cudy TR3000 v1 | `cudy_tr3000-v1` | aarch64_cortex-a53 | 128MB | толстый | UPX |

### 12.2 Алгоритм (12 шагов)

**Шаг 0: Подключение + автоопределение модели**
```bash
ping -c 2 -W 2 192.168.1.1
MODEL=$(ssh -o StrictHostKeyChecking=no root@192.168.1.1 "cat /tmp/sysinfo/model" 2>/dev/null)
echo "Модель: $MODEL"
```

**Шаг 1: Заливка OpenWrt** — SCP прошивки на роутер, sysupgrade, ожидание перезагрузки.

**Шаг 2: Создание backup-шаблона** — настройка timezone, hostname, пароля, создание backup.

**Шаг 3: Применить шаблон + hostname** — распаковка backup, установка hostname, reboot.

**Шаг 4: Создать ключ main** — через relay-сервер (см. скилл create_clone_key).

**Шаг 5: Установка Podkop** — через itdog install.sh:
```bash
printf 'y\ny\nru\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh)
```

**Шаг 6: Настройка Podkop** — UCI настройки, community lists, proxy_string.

**Шаг 7: Установка Tailscale** — из репозитория gunano, fw_mode=none, init.d DISABLED.

**Шаг 8: Спасительные скрипты** — rc.local, firewall, watchdog'ы, crontab, check-ip, fw4-fix.

**Шаг 9: Запуск Tailscale + авторизация** — запуск tailscaled, получение ссылки, ожидание зелёной точки.

**Шаг 10: Проверка перед ребутом** — 5 пунктов (fw_mode, init.d, rc.local, watchdog, exclude_ntp).

**Шаг 11: Ребут + мониторинг** — reboot, ожидание, мониторинг каждые 5 сек (Proxy, TS, Ping).

**Шаг 12: Финальная диагностика** — `check-ip` с роутера (loc=не RU).

### 12.3 Железные правила (для всех прошивок)

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

## 13. Скилл: Прошивка Xiaomi AX3000T

### 13.1 Особенности Xiaomi AX3000T

- **НЕ Cudy M3000** — прошивка другая (`xiaomi_mi-router-ax3000t`, не `cudy_m3000`)
- **Нет v1/v2 разделения** — одна прошивка для всех ревизий
- **initramfs не нужен** — sysupgrade с загрузчика (через SSH)
- **Первый вход** — через SSH на 192.168.1.1 (без пароля)

### 13.2 ⚠️ ВАЖНО: Смена LAN IP на OpenWrt 25.12 (apk)

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

### 13.3 🔍 ВАЖНО: Проверка WAN после каждой операции

После **каждой значимой операции** — **обязательно проверять интернет на WAN порту**.

```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@<ROUTER_IP> "
echo '=== WAN STATUS ==='
ubus call network.interface.wan status 2>/dev/null | grep -E '\"device\"|\"address\"|\"method\"' | head -5
echo ''
echo '=== ПИНГ ДО ДНС ==='
ping -c 2 -W 3 1.1.1.1 2>&1 | tail -3
echo ''
echo '=== ПИНГ ДО GOOGLE ==='
ping -c 2 -W 3 google.com 2>&1 | tail -3
"
```

### 13.4 Алгоритм прошивки (12 шагов)

Полный алгоритм — в скилле `flash_xiaomi_ax3000t.md`. Кратко:
1. Проверка роутера (модель, версия)
2. Заливка OpenWrt 25.12.2 через SCP
3. Создание backup-шаблона (timezone, пароль, hostname)
4. Применить шаблон + hostname
5. Создать ключ main через relay
6. Установка Podkop (толстый sing-box)
7. Настройка Podkop (один профиль main)
8. Установка Tailscale из gunano
9. Спасительные скрипты + watchdog + fw4-fix + check-ip
10. Запуск Tailscale + авторизация
11. Проверка перед ребутом (5 пунктов)
12. Ребут + мониторинг + финальная диагностика

### 13.5 Важные отличия от Cudy M3000

| Параметр | Cudy M3000 | Xiaomi AX3000T |
|----------|-----------|----------------|
| Прошивка | `cudy_m3000-v1` | `xiaomi_mi-router-ax3000t` |
| Backup-шаблон | `backup-m3000-template.tar.gz` | `backup-ax3000t-template.tar.gz` |
| v1/v2 | Есть (по серийнику) | Нет разделения |
| Первый вход | 192.168.1.1 без пароля | 192.168.1.1 без пароля |
| После шаблона | 192.168.5.1 (пароль 56756789) | 192.168.5.1 (пароль 56756789) |

### 13.6 Уроки с 19-ternovsky (Xiaomi AX3000T)

1. **Podkop status = not running** — это нормально для OpenWrt 25.12
2. **download_lists_via_proxy=0** — иначе sing-box падает при загрузке списков
3. **raw.githubusercontent.com блокируется** — нужен podkop-fix-lists.sh
4. **fw4-fix обязателен** — иначе forwarded трафик (с клиентов) не маркируется
5. **fakeIP (198.18.0.0/15)** — это нормально, так работает podkop/sing-box
6. **enable_output_network_interface=1** — чтобы трафик с самого роутера тоже шёл через прокси

### 13.7 Хронология ребута (подтверждено замерами)

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

### 13.8 Последовательность после ребута (гарантированная)

```
0-30 сек:  Загрузка OpenWrt
30-40 сек: Podkop стартует → интернет через CZ2 есть
40-45 сек: rc.local запускает tailscaled с --tun=userspace-networking
45-60 сек: tailscaled подключается к controlplane через CZ2 → зелёная точка
```

---

## 14. Скилл: Создание ключа-клона

### 14.1 Алгоритм

**Шаг 1. Получить текущий proxy_string с роутера:**
```bash
sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@<TAILSCALE_IP> "
uci get podkop.main.proxy_string
"
```
Из строки извлечь: relay_ip, relay_port, pbk, sid, sni, fp.

**Шаг 2. Определить, на каком X-UI сервере создавать клиента:**
- Если pbk известен — найти сервер по pbk
- Если pbk НЕ известен — найти сервер по IP

**Шаг 3. Посмотреть список инбаундов на сервере:**
Зайти на панель через браузер: `https://<SERVER_IP>:5050/5050/`
Логин: `ad` / пароль: `56`

**Шаг 4. Создать нового клиента через `create_vless_key.py`:**
```bash
python3 /Users/vas/CLAUDECODE/tools/create_vless_key.py \
  --router <ROUTER_NAME> \
  --panel-ip <PANEL_HOST> \
  --panel-port 5050 \
  --inbound-id <INBOUND_ID> \
  --relay-ip <RELAY_IP> \
  --relay-port <RELAY_PORT> \
  --pbk "<PBK>" \
  --sid "<SID>"
```

**Шаг 5. Проверить новый ключ:**
```bash
python3 /Users/vas/CLAUDECODE/check_vless.py "vless://<NEW_UUID>@..."
```
Должен быть **TCP OK** + **TLS OK** → **READY**.

**Шаг 6. Заменить ключ на роутере (без перезагрузки Podkop):**
```bash
sshpass -p '56756789' ssh ... root@<TAILSCALE_IP> "
uci set podkop.main.proxy_string='vless://<NEW_UUID>@...'
uci commit podkop
"
```
**НЕ перезагружать podkop.** Только `uci set` + `uci commit`.

### 14.2 Почему НЕЛЬЗЯ использовать API напрямую через curl

1. **X-UI API нестабилен** — разные версии панелей имеют разные эндпоинты
2. **Ошибка аутентификации** — куки могут не сохраниться, сессия истекает
3. **Нет проверок** — можно случайно создать дубликат или сломать конфиг
4. **Нет лимитов** — можно создать клиента без expiryTime/totalGB

Использовать только `create_vless_key.py` — он:
- Правильно логинится
- Проверяет существующих клиентов
- Ставит корректные лимиты (365 дней / 1 TB)
- Генерирует правильный VLESS URL

### 14.3 Железные правила (дополнение)

1. **Ключ-клон = тот же сервер + тот же порт + тот же pbk + тот же sid + новый UUID**
2. **НЕ создавать новый профиль** — заменять UUID в существующем
3. **НЕ перезагружать podkop** после замены ключа — только uci commit
4. **НЕ использовать curl к API** — только create_vless_key.py
5. **Всегда проверять ключ** через check_vless.py перед установкой

---

## 15. Скилл: Установка podkop

### 15.1 Проверка совместимости

```bash
cat /etc/openwrt_release | grep DISTRIB_RELEASE
# Должно быть: 25.12.0 — значит apk
# Если 24.x — нужен opkg и .ipk пакеты
```

### 15.2 Установка

```bash
printf 'y\ny\nru\n' | sh <(wget -O - https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh)
```

### 15.3 Настройка через UCI

```bash
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

# Community lists
uci del podkop.main.community_lists 2>/dev/null || true
uci add_list podkop.main.community_lists='telegram'
uci add_list podkop.main.community_lists='meta'
uci add_list podkop.main.community_lists='youtube'
for l in geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront; do
  uci add_list podkop.main.community_lists="$l"
done

# Main proxy
uci set podkop.main.proxy_string='<VLESS_MAIN_KEY>'
uci set podkop.main.proxy_config_type='url'
uci set podkop.main.mixed_proxy_enabled='0'

uci commit podkop
/etc/init.d/podkop restart
```

---

## 16. Тулз: Спасительный скрипт (rescue_generic.sh)

**Назначение:** Базовая стабилизация роутера. Применяется когда роутер "сыпется" — Tailscale отваливается, часы дрейфуют, podkop падает.

**Запуск:**
```bash
cat rescue_generic.sh | ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@100.x.x.x sh -s
```

**Что делает:**
1. `fw_mode=none` — иначе Tailscale убивает маршрутизацию
2. `init.d/tailscale DISABLED` — иначе при ребуте Tailscale стартует раньше сети
3. WAN ifname — проверка и добавление (podkop использует ifname, а не device)
4. `exclude_ntp=1` — иначе NTP ломает синхронизацию
5. `enable_output_network_interface=1` — трафик с роутера через прокси
6. `rc.local` с tailscaled (sleep 40)
7. **3 watchdog'а на 2 минуты:**
   - `ts-watchdog.sh` — следит за tailscaled, восстанавливает rc.local
   - `podkop-watchdog.sh` — следит за sing-box, перезапускает podkop если упал
   - `route-watchdog.sh` — следит за PodkopTable в nftables
8. Crontab со всеми watchdog'ами + обновление списков каждые 3 часа
9. `check-ip` скрипт диагностики

**Полный код скрипта (rescue_generic.sh):**

```bash
#!/bin/sh
# Универсальный спасительный скрипт
# Применяется через SSH, НЕ перезагружает Tailscale, НЕ перезапускает podkop
# Только фиксы + 3 watchdog'а на 2 минуты
#
# Запуск: cat rescue_generic.sh | ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@100.x.x.x sh -s
#
# Железное правило: Tailscale НЕ ТРОГАЕМ, ничего НЕ ПЕРЕЗАГРУЖАЕМ

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   УНИВЕРСАЛЬНЫЙ СПАСИТЕЛЬНЫЙ СКРИПТ             ║"
echo "║   Tailscale НЕ ТРОГАЕМ • Podkop НЕ РЕСТАРТИМ    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ===== 1. Tailscale fw_mode = none =====
echo "[1/9] Tailscale fw_mode → none"
CURRENT_FW=$(uci get tailscale.settings.fw_mode 2>/dev/null)
if [ "$CURRENT_FW" != "none" ]; then
    uci set tailscale.settings.fw_mode='none'
    uci commit tailscale
    echo "  ✓ fw_mode: $CURRENT_FW → none"
else
    echo "  ✓ fw_mode уже none"
fi

# ===== 2. init.d/tailscale DISABLED =====
echo "[2/9] init.d/tailscale → DISABLED"
if /etc/init.d/tailscale enabled 2>/dev/null; then
    /etc/init.d/tailscale disable
    echo "  ✓ init.d/tailscale disabled"
else
    echo "  ✓ init.d/tailscale уже disabled"
fi

# ===== 3. WAN ifname =====
echo "[3/9] WAN ifname → проверка"
WAN_IFNAME=$(uci get network.wan.ifname 2>/dev/null)
if [ -z "$WAN_IFNAME" ]; then
    WAN_DEVICE=$(uci get network.wan.device 2>/dev/null)
    if [ -n "$WAN_DEVICE" ]; then
        uci set network.wan.ifname="$WAN_DEVICE"
        uci commit network
        echo "  ✓ network.wan.ifname=$WAN_DEVICE (добавлен из device)"
    else
        echo "  ⚠️ WAN device не найден, пропускаем"
    fi
else
    echo "  ✓ network.wan.ifname=$WAN_IFNAME (уже есть)"
fi

# ===== 4. exclude_ntp = 1 + enable_output_network_interface = 1 =====
echo "[4/9] Podkop exclude_ntp → 1"
CURRENT_NTP=$(uci get podkop.settings.exclude_ntp 2>/dev/null)
if [ "$CURRENT_NTP" != "1" ]; then
    uci set podkop.settings.exclude_ntp='1'
    echo "  ✓ exclude_ntp: $CURRENT_NTP → 1"
else
    echo "  ✓ exclude_ntp уже 1"
fi

echo "      enable_output_network_interface → 1"
CURRENT_OUTPUT=$(uci get podkop.settings.enable_output_network_interface 2>/dev/null)
if [ "$CURRENT_OUTPUT" != "1" ]; then
    uci set podkop.settings.enable_output_network_interface='1'
    echo "  ✓ enable_output_network_interface: $CURRENT_OUTPUT → 1"
else
    echo "  ✓ enable_output_network_interface уже 1"
fi
uci commit podkop

# ===== 5. rc.local с tailscaled =====
echo "[5/9] rc.local → проверка/создание"
if [ -f /etc/rc.local ] && grep -q "tailscaled" /etc/rc.local 2>/dev/null; then
    echo "  ✓ rc.local уже содержит tailscaled"
else
    [ -f /etc/rc.local ] && cp /etc/rc.local /etc/rc.local.bak 2>/dev/null
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
    echo "  ✓ rc.local создан"
fi

# ===== 6. firewall → tailscale0 в LAN зону =====
echo "[6/9] firewall → tailscale0 в LAN зону"
CURRENT_DEV=$(uci get firewall.@zone[0].device 2>/dev/null)
if echo "$CURRENT_DEV" | grep -q "tailscale0"; then
    echo "  ✓ tailscale0 уже в LAN зоне"
else
    uci set firewall.@zone[0].device='br-lan tailscale0' 2>/dev/null
    uci commit firewall 2>/dev/null
    echo "  ✓ tailscale0 добавлен в LAN зону (конфиг сохранён, firewall НЕ перезагружен)"
fi

# ===== 7. Три watchdog'а на 2 минуты =====
echo "[7/9] Watchdog'ы (3 шт, каждая 2 мин)..."

# Tailscale watchdog
cat > /etc/ts-watchdog.sh << 'WEOF'
#!/bin/sh
RC_BACKUP="/etc/rc.local.bak"
if [ ! -f "$RC_BACKUP" ]; then exit 1; fi
if ! grep -q "tailscaled" /etc/rc.local 2>/dev/null; then
    cp "$RC_BACKUP" /etc/rc.local
fi
if ! ps | grep -q "tailscaled --state="; then
    (sleep 5; tailscaled --state=/etc/tailscale/tailscaled.state --tun=userspace-networking --statedir=/etc/tailscale/ >> /tmp/ts.log 2>&1 & sleep 5; tailscale up --accept-dns=false --accept-routes) &
fi
WEOF
chmod +x /etc/ts-watchdog.sh
echo "  ✓ ts-watchdog.sh"

# Podkop watchdog
cat > /etc/podkop-watchdog.sh << 'WEOF'
#!/bin/sh
if ! ps | grep -q "sing-box run"; then
    logger -t podkop-watchdog "sing-box not running, restarting podkop"
    /etc/init.d/podkop restart
fi
WEOF
chmod +x /etc/podkop-watchdog.sh
echo "  ✓ podkop-watchdog.sh"

# Route watchdog
cat > /etc/route-watchdog.sh << 'WEOF'
#!/bin/sh
nft list table inet PodkopTable >/dev/null 2>&1 || {
    logger -t route-watchdog "PodkopTable missing, restarting podkop"
    /etc/init.d/podkop restart
}
WEOF
chmod +x /etc/route-watchdog.sh
echo "  ✓ route-watchdog.sh"

# ===== 8. Crontab =====
echo "[8/9] Crontab → 3 watchdog'а + обновление списков"
(
    crontab -l 2>/dev/null | grep -v -E "(ts-watchdog|podkop-watchdog|route-watchdog|list_update)"
    echo "*/2 * * * * /etc/ts-watchdog.sh"
    echo "*/2 * * * * /etc/podkop-watchdog.sh"
    echo "*/2 * * * * /etc/route-watchdog.sh"
    echo "13 */3 * * * /usr/bin/podkop list_update"
) | crontab -
echo "  ✓ crontab обновлён"

# ===== 9. check-ip скрипт диагностики =====
echo "[9/9] check-ip → скрипт диагностики"
cat > /usr/bin/check-ip << 'CIPEOF'
#!/bin/sh
echo '╔══════════════════════════════════════════════╗'
echo '║              CHECK-IP                        ║'
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
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://$url 2>/dev/null)
  TIME=$(curl -s -o /dev/null -w '%{time_total}' --max-time 8 https://$url 2>/dev/null)
  printf '%-15s %3s  (%ss)\n' "$url" "$CODE" "$TIME"
done
CIPEOF
chmod +x /usr/bin/check-ip
echo "  ✓ /usr/bin/check-ip создан"

# ===== ФИНАЛ =====
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ СПАСЕНИЕ ПРИМЕНЕНО                           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Проверка:"
echo "  fw_mode:      $(uci get tailscale.settings.fw_mode)"
echo "  exclude_ntp:  $(uci get podkop.settings.exclude_ntp)"
echo "  init.d:       $(/etc/init.d/tailscale enabled 2>/dev/null && echo 'ENABLED' || echo 'DISABLED')"
echo "  watchdog:     $(crontab -l | grep -c watchdog) записи"
echo "  check-ip:     $(which check-ip 2>/dev/null || echo 'НЕ НАЙДЕН')"
echo ""
echo "Для проверки IP выполните: check-ip"
```

---

## 17. Тулз: Фикс блокировки GitHub CDN (podkop-fix-lists.sh)

**Назначение:** Чинит обновление community листов podkop, когда провайдер блокирует `raw.githubusercontent.com`.

**Проблема:** Провайдер блокирует `raw.githubusercontent.com` на уровне DPI (SNI). Из 4 IP-адресов Fastly CDN (185.199.108-111.133) некоторые могут быть заблокированы.

**Решение:** Скрипт проверяет каждый IP, добавляет только рабочие в `/etc/hosts`, и запускает `podkop list_update`.

**Запуск:**
```bash
# Установка на роутер
wget -q -O /root/podkop-fix-lists.sh \
  "https://raw.githubusercontent.com/vasneverov/openwrt-scripts/main/tools/podkop-fix-lists.sh"
chmod +x /root/podkop-fix-lists.sh
sh /root/podkop-fix-lists.sh

# Добавить в cron
echo "0 3 * * * /bin/sh /root/podkop-fix-lists.sh --cron" >> /etc/crontabs/root
```

**Полный код скрипта (podkop-fix-lists.sh):**

```bash
#!/bin/sh
# podkop-fix-lists.sh — починить обновление community листов podkop
#
# Использование:
#   sh podkop-fix-lists.sh                  # проверить и починить
#   sh podkop-fix-lists.sh --check-only     # только проверить, не чинить
#   sh podkop-fix-lists.sh --cron           # тихий режим для cron

set -e

# Цвета (если терминал поддерживает)
if [ -t 1 ]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; NC=''
fi

info()  { printf "${GREEN}[✓]${NC} %s\n" "$1"; }
warn()  { printf "${YELLOW}[!]${NC} %s\n" "$1"; }
error() { printf "${RED}[✗]${NC} %s\n" "$1"; }
log()   { printf "  %s\n" "$1"; }

RAW_IPS="185.199.108.133 185.199.109.133 185.199.110.133 185.199.111.133"
HOSTS_FILE="/etc/hosts"
DOMAIN="raw.githubusercontent.com"
TEST_URL="https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Subnets/IPv4/meta.lst"

echo "=============================================="
echo "  podkop-fix-lists.sh — починить списки podkop"
echo "=============================================="
echo ""

# Шаг 1: Проверка DNS
echo "--- Шаг 1: DNS резолвинг ---"
DNS_IPS=""
if command -v nslookup >/dev/null 2>&1; then
    DNS_IPS=$(nslookup "$DOMAIN" 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | sort -u | tr '\n' ' ')
fi
if [ -n "$DNS_IPS" ]; then
    info "DNS резолвит $DOMAIN в: $DNS_IPS"
else
    warn "Не удалось получить DNS-записи для $DOMAIN"
fi

# Шаг 2: Проверка /etc/hosts
echo ""; echo "--- Шаг 2: /etc/hosts ---"
HOSTS_ENTRIES=$(grep -i "$DOMAIN" "$HOSTS_FILE" 2>/dev/null || true)
if [ -n "$HOSTS_ENTRIES" ]; then
    info "Записи в /etc/hosts найдены"
else
    warn "/etc/hosts не содержит записей для $DOMAIN"
fi

# Шаг 3: Проверка доступности IP
echo ""; echo "--- Шаг 3: Проверка доступности IP ---"
WORKING_IPS=""; BROKEN_IPS=""
for ip in $RAW_IPS; do
    if curl -sL --max-time 5 --resolve "$DOMAIN:443:$ip" "$TEST_URL" -o /dev/null -w "%{http_code}" 2>/dev/null | grep -q "200"; then
        WORKING_IPS="$WORKING_IPS $ip"
        info "$ip — доступен"
    else
        BROKEN_IPS="$BROKEN_IPS $ip"
        error "$ip — недоступен"
    fi
done

# Шаг 4: Исправление /etc/hosts
echo ""; echo "--- Шаг 4: Исправление ---"
if grep -qi "$DOMAIN" "$HOSTS_FILE" 2>/dev/null; then
    warn "Удаляю старые записи $DOMAIN из /etc/hosts"
    grep -v -i "$DOMAIN" "$HOSTS_FILE" > "$HOSTS_FILE.tmp" && mv "$HOSTS_FILE.tmp" "$HOSTS_FILE"
fi

COUNT=0
for ip in $WORKING_IPS; do
    echo "$ip $DOMAIN" >> "$HOSTS_FILE"
    COUNT=$((COUNT + 1))
done

if [ "$COUNT" -gt 0 ]; then
    info "Добавлено $COUNT рабочих IP в /etc/hosts"
else
    warn "Ни один IP не работает! Добавляю все IP на всякий случай."
    for ip in $RAW_IPS; do
        echo "$ip $DOMAIN" >> "$HOSTS_FILE"
    done
fi

# Шаг 5: Проверка после исправления
echo ""; echo "--- Шаг 5: Проверка после исправления ---"
if curl -sL --max-time 10 "$TEST_URL" -o /dev/null -w "%{http_code}" 2>/dev/null | grep -q "200"; then
    info "curl: OK — $DOMAIN доступен"
else
    error "curl: $DOMAIN всё ещё недоступен"
fi

# Шаг 6: Запуск обновления podkop
echo ""; echo "--- Шаг 6: Обновление podkop ---"
if command -v /usr/bin/podkop >/dev/null 2>&1; then
    info "Запускаю podkop list_update..."
    /usr/bin/podkop list_update 2>&1 || warn "podkop list_update завершился с ошибкой"
else
    warn "podkop не найден"
fi

echo ""; echo "=============================================="
echo "  ГОТОВО"
echo "=============================================="
echo ""
echo "Итоговые записи в /etc/hosts:"
grep -i "$DOMAIN" "$HOSTS_FILE" 2>/dev/null || echo "(нет записей)"
```

---

## 18. Тулз: Фикс forwarded трафика (podkop-fw4-fix.sh)

**Назначение:** Фикс для podkop на OpenWrt 25.12 (fw4/nftables). Добавляет правила маркировки в `inet fw4 mangle_forward` (hook forward), который гарантированно видит forwarded трафик.

**Проблема:** На OpenWrt 25.12 (ядро 6.12, fw4/nftables) таблица `inet PodkopTable` с `hook prerouting` НЕ ВИДИТ forwarded трафик (с клиентов WiFi/LAN). Это известное ограничение: inet таблицы с prerouting видят только local трафик.

**Установка:**
```bash
cat tools/podkop-fw4-fix.sh | ssh root@ROUTER_IP "cat > /root/podkop-fw4-fix.sh && chmod +x /root/podkop-fw4-fix.sh"
ssh root@ROUTER_IP "/root/podkop-fw4-fix.sh install"
```

**После обновления podkop листов:**
```bash
/root/podkop-fw4-fix.sh update
```

**Полный код скрипта (podkop-fw4-fix.sh):**

```bash
#!/bin/sh
# podkop-fw4-fix.sh — фикс для podkop на OpenWrt 25.12 (fw4/nftables)
#
# ПРОБЛЕМА:
# На OpenWrt 25.12 (ядро 6.12, fw4/nftables) таблица inet PodkopTable
# с hook prerouting НЕ ВИДИТ forwarded трафик (с клиентов WiFi/LAN).
# Это известное ограничение: inet таблицы с prerouting видят только local трафик.
#
# Forwarded трафик видят:
#   - ip/ip6 таблицы с hook prerouting
#   - inet таблицы с hook forward
#
# РЕШЕНИЕ:
# Добавляем правила маркировки в inet fw4 mangle_forward (hook forward),
# который гарантированно видит forwarded трафик.
#
# Установка:
#   cat tools/podkop-fw4-fix.sh | ssh root@ROUTER_IP "cat > /root/podkop-fw4-fix.sh && chmod +x /root/podkop-fw4-fix.sh"
#   ssh root@ROUTER_IP "/root/podkop-fw4-fix.sh install"
#
# После обновления podkop листов:
#   /root/podkop-fw4-fix.sh update

PODKOP_TABLE="inet PodkopTable"
PODKOP_SET="podkop_subnets"
FW4_TABLE="inet fw4"
FW4_CHAIN="mangle_forward"
FW4_SET="podkop_subnets_fwd"
INTERFACE="br-lan"
MARK="0x00100000"

log() {
    echo "[podkop-fw4-fix] $1"
    logger -t podkop-fw4-fix "$1"
}

install_service() {
    cat > /etc/init.d/podkop-fw4-fix << 'INITEOF'
#!/bin/sh /etc/rc.common

START=99
STOP=

boot() {
    /root/podkop-fw4-fix.sh update
}

start() {
    /root/podkop-fw4-fix.sh update
}

reload() {
    /root/podkop-fw4-fix.sh update
}
INITEOF
    chmod +x /etc/init.d/podkop-fw4-fix
    /etc/init.d/podkop-fw4-fix enable
    log "init.d script installed and enabled"
}

update() {
    log "Updating mark rules in $FW4_TABLE $FW4_CHAIN..."

    # 1. Create set in inet fw4 if not exists
    nft add set $FW4_TABLE $FW4_SET '{ type ipv4_addr; flags interval; auto-merge; }' 2>/dev/null || true

    # 2. Flush old elements from set
    nft flush set $FW4_TABLE $FW4_SET 2>/dev/null || true

    # 3. Copy elements from inet PodkopTable podkop_subnets
    ELEMENTS=$(nft list set $PODKOP_TABLE $PODKOP_SET 2>/dev/null | \
        tr "\n" " " | \
        sed 's/.*elements = {/{/' | \
        sed 's/}.*/}/')
    if [ -n "$ELEMENTS" ] && [ "$ELEMENTS" != "{}" ]; then
        nft add element $FW4_TABLE $FW4_SET "$ELEMENTS" 2>/dev/null
        COUNT=$(echo "$ELEMENTS" | grep -o ',' | wc -l)
        COUNT=$((COUNT + 1))
        log "Copied $COUNT elements to $FW4_TABLE $FW4_SET"
    else
        log "WARNING: could not get elements from $PODKOP_TABLE $PODKOP_SET"
    fi

    # 4. Delete old rules from inet fw4 mangle_forward (by handle)
    RULES=$(nft -a list chain $FW4_TABLE $FW4_CHAIN 2>/dev/null | grep 'podkop-fw4-fix' | grep -o 'handle [0-9]*' | awk '{print $2}')
    for handle in $RULES; do
        nft delete rule $FW4_TABLE $FW4_CHAIN handle $handle 2>/dev/null || true
    done

    # 5. Add new mark rules in mangle_forward (hook forward — видит forwarded трафик)
    nft add rule $FW4_TABLE $FW4_CHAIN \
        iifname "$INTERFACE" ip daddr @$FW4_SET meta l4proto tcp \
        meta mark set $MARK counter \
        comment "podkop-fw4-fix-forward-tcp"

    nft add rule $FW4_TABLE $FW4_CHAIN \
        iifname "$INTERFACE" ip daddr @$FW4_SET meta l4proto udp \
        meta mark set $MARK counter \
        comment "podkop-fw4-fix-forward-udp"

    nft add rule $FW4_TABLE $FW4_CHAIN \
        iifname "$INTERFACE" ip daddr 198.18.0.0/15 meta l4proto tcp \
        meta mark set $MARK counter \
        comment "podkop-fw4-fix-forward-fakeip-tcp"

    nft add rule $FW4_TABLE $FW4_CHAIN \
        iifname "$INTERFACE" ip daddr 198.18.0.0/15 meta l4proto udp \
        meta mark set $MARK counter \
        comment "podkop-fw4-fix-forward-fakeip-udp"

    log "Mark rules updated in $FW4_TABLE $FW4_CHAIN"
    nft list chain $FW4_TABLE $FW4_CHAIN 2>/dev/null | grep 'podkop-fw4-fix'
}

case "${1:-}" in
    install)
        log "Installing podkop-fw4-fix..."
        update
        install_service
        log "Installation complete"
        ;;
    update)
        update
        ;;
    remove)
        log "Removing podkop-fw4-fix..."
        /etc/init.d/podkop-fw4-fix disable 2>/dev/null || true
        rm -f /etc/init.d/podkop-fw4-fix
        RULES=$(nft -a list chain $FW4_TABLE $FW4_CHAIN 2>/dev/null | grep 'podkop-fw4-fix' | grep -o 'handle [0-9]*' | awk '{print $2}')
        for handle in $RULES; do
            nft delete rule $FW4_TABLE $FW4_CHAIN handle $handle 2>/dev/null || true
        done
        nft delete set $FW4_TABLE $FW4_SET 2>/dev/null || true
        log "Removal complete"
        ;;
    *)
        echo "Usage: $0 {install|update|remove}"
        echo ""
        echo "  install - install fix and init.d script"
        echo "  update  - update mark rules (after podkop list update)"
        echo "  remove  - remove fix"
        ;;
esac
```

---

## 19. Тулз: Создание VLESS ключа (create_vless_key.py)

**Назначение:** Универсальный скрипт для создания VLESS ключей на X-UI панелях. Правильно логинится, проверяет существующих клиентов, ставит корректные лимиты (365 дней / 1 TB).

**Использование:**
```bash
# По предустановленной панели
python3 create_vless_key.py --router rom5office --panel fin3
python3 create_vless_key.py --router myrouter --panel begetspb --inbound 4

# Ручная настройка
python3 create_vless_key.py \
  --router <ROUTER_NAME> \
  --panel-ip <PANEL_HOST> \
  --panel-port 5050 \
  --inbound-id <INBOUND_ID> \
  --relay-ip <RELAY_IP> \
  --relay-port <RELAY_PORT> \
  --pbk "<PBK>" \
  --sid "<SID>"
```

**Предустановленные панели:**
- `fin3` — 144.31.66.115:5050, inbound 3, relay 5.35.84.151:4191
- `begetspb` — 5.35.84.151:5050, inbound 1, relay 5.35.84.151:6443
- `begetspb-yt` — 5.35.84.151:5050, inbound 4, relay 5.35.84.151:8853

**Полный код скрипта (create_vless_key.py):**

```python
#!/usr/bin/env python3
"""
Универсальный скрипт для создания VLESS ключей на X-UI панелях.

Использование:
    python3 create_vless_key.py --router rom5office --panel fin3
    python3 create_vless_key.py --router myrouter --panel begetspb --inbound 4

Панели (predifined):
    - fin3: 144.31.66.115:5050, inbound 3 (WL_rout_fin3_4191)
    - begetspb: 5.35.84.151:5050, inbound 1 (main)
    - begetspb-yt: 5.35.84.151:5050, inbound 4 (YouTube direct)

Ручная настройка:
    --panel-ip, --panel-port, --inbound-id, --relay-ip, --relay-port, --pbk, --sid
"""

import argparse
import asyncio
import json
import ssl
import uuid
import sys
import time

# Предустановленные конфигурации панелей
PANELS = {
    "fin3": {
        "ip": "144.31.66.115",
        "port": "5050",
        "inbound_id": 3,
        "label": "Fin3",
        "relay_ip": "5.35.84.151",
        "relay_port": "4191",
        "pbk": "XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw",
        "sid": "932e706c",
        "default_expiry_days": 365,
        "default_traffic_gb": 1000,
    },
    "begetspb": {
        "ip": "5.35.84.151",
        "port": "5050",
        "inbound_id": 1,
        "label": "bSPB_direct",
        "relay_ip": "5.35.84.151",
        "relay_port": "6443",
        "pbk": "me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM",
        "sid": "ddcb53b3",
    },
    "begetspb-yt": {
        "ip": "5.35.84.151",
        "port": "5050",
        "inbound_id": 4,
        "label": "bSPB_direct_8853",
        "relay_ip": "5.35.84.151",
        "relay_port": "8853",
        "pbk": "me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM",
        "sid": "ddcb53b3",
    },
}

USERNAME = "ad"
PASSWORD = "56"
SNI = "www.apple.com"


def create_vless_key(uuid_str, relay_ip, relay_port, pbk, sid, label):
    """Generate VLESS key URL."""
    return (
        f"vless://{uuid_str}@{relay_ip}:{relay_port}?"
        f"type=grpc&security=reality&mode=gun&serviceName=&"
        f"pbk={pbk}&sid={sid}&sni={SNI}&fp=chrome&spx=%2F"
        f"#{label}"
    )


async def create_key(router_name, panel_config, custom_email=None, dry_run=False):
    """Create VLESS key on X-UI panel."""
    panel_ip = panel_config["ip"]
    panel_port = panel_config["port"]
    inbound_id = panel_config["inbound_id"]
    relay_ip = panel_config["relay_ip"]
    relay_port = panel_config["relay_port"]
    pbk = panel_config["pbk"]
    sid = panel_config["sid"]
    label_base = panel_config["label"]

    if custom_email:
        email = custom_email
    else:
        email = f"{router_name}-{label_base.lower().replace('_', '-')}"

    print(f"🔐 Connecting to panel {panel_ip}:{panel_port}...")
    print(f"📧 Email will be: {email}")

    if dry_run:
        print("📝 DRY RUN: Would create client with above email")
        return None

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        import aiohttp
    except ImportError:
        print("❌ Error: aiohttp not installed. Run: pip install aiohttp")
        sys.exit(1)

    base_url = f"https://{panel_ip}:{panel_port}/{panel_port}"

    async with aiohttp.ClientSession() as session:
        # Login
        login_url = f"{base_url}/login"
        resp = await session.post(login_url, json={"username": USERNAME, "password": PASSWORD}, ssl=ctx)

        if resp.status != 200:
            print(f"❌ Login failed: HTTP {resp.status}")
            return None

        set_cookie = resp.headers.get("Set-Cookie", "")
        if "3x-ui=" not in set_cookie:
            print("❌ Login failed: No 3x-ui cookie in response")
            return None

        cookie = set_cookie.split("3x-ui=")[1].split(";")[0]
        print(f"✅ Logged in")

        headers = {"Cookie": f"3x-ui={cookie}"}

        # Get existing clients
        print(f"\n📋 Checking inbound {inbound_id}...")
        get_url = f"{base_url}/panel/api/inbounds/get/{inbound_id}"
        resp = await session.get(get_url, headers=headers, ssl=ctx)

        if resp.status != 200:
            print(f"❌ Failed to get inbound: HTTP {resp.status}")
            return None

        data = await resp.json(content_type=None)
        inbound = data.get("obj", {})
        settings = json.loads(inbound.get("settings", "{}"))
        clients = settings.get("clients", [])

        print(f"Found {len(clients)} existing clients")

        # Check if email already exists
        for c in clients:
            if c.get("email") == email:
                print(f"⚠️ Client with email '{email}' already exists!")
                existing_uuid = c.get("id")
                print(f"   Existing UUID: {existing_uuid}")
                key = create_vless_key(existing_uuid, relay_ip, relay_port, pbk, sid, email)
                return key

        # Generate new UUID
        new_uuid = str(uuid.uuid4())
        print(f"\n🆕 Generated UUID: {new_uuid}")

        # Calculate limits
        expiry_days = panel_config.get("default_expiry_days", 365)
        traffic_gb = panel_config.get("default_traffic_gb", 1000)

        expiry_ms = int((time.time() + expiry_days * 24 * 60 * 60) * 1000)
        traffic_bytes = int(traffic_gb * 1024 * 1024 * 1024)

        print(f"⏱️  Expiry: {expiry_days} days")
        print(f"📊 Traffic limit: {traffic_gb} GB")

        # Create payload
        payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [
                    {
                        "id": new_uuid,
                        "email": email,
                        "limitIp": 0,
                        "enable": True,
                        "expiryTime": expiry_ms,
                        "totalGB": traffic_bytes,
                        "tgId": "",
                        "subId": "",
                        "comment": "",
                    }
                ]
            }),
        }

        # Add client
        print(f"\n📝 Adding client...")
        add_url = f"{base_url}/panel/api/inbounds/addClient"
        resp = await session.post(add_url, json=payload, headers=headers, ssl=ctx)

        if resp.status != 200:
            text = await resp.text()
            print(f"❌ Failed to add client: HTTP {resp.status} - {text}")
            return None

        result = await resp.json(content_type=None)
        if result.get("success"):
            print(f"✅ Client added successfully!")
            key = create_vless_key(new_uuid, relay_ip, relay_port, pbk, sid, email)
            return key
        else:
            print(f"❌ API error: {result}")
            return None


def main():
    parser = argparse.ArgumentParser(
        description="Create VLESS key for router on X-UI panel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--router", "-r", required=True, help="Router name/identifier")
    parser.add_argument("--panel", "-p", choices=list(PANELS.keys()), help="Predefined panel config")
    parser.add_argument("--email", "-e", help="Custom email")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be done without creating")

    # Manual panel configuration
    parser.add_argument("--panel-ip", help="Panel IP address")
    parser.add_argument("--panel-port", default="5050", help="Panel port (default: 5050)")
    parser.add_argument("--inbound-id", type=int, help="Inbound ID")
    parser.add_argument("--relay-ip", help="Relay/connect IP for VLESS key")
    parser.add_argument("--relay-port", help="Relay port for VLESS key")
    parser.add_argument("--pbk", help="Public key for REALITY")
    parser.add_argument("--sid", help="Short ID for REALITY")

    args = parser.parse_args()

    # Build panel config
    if args.panel:
        panel_config = PANELS[args.panel].copy()
        print(f"📡 Using predefined panel: {args.panel}")
    elif args.panel_ip and args.inbound_id and args.relay_ip and args.relay_port and args.pbk and args.sid:
        panel_config = {
            "ip": args.panel_ip,
            "port": args.panel_port,
            "inbound_id": args.inbound_id,
            "relay_ip": args.relay_ip,
            "relay_port": args.relay_port,
            "pbk": args.pbk,
            "sid": args.sid,
            "label": "custom",
        }
        print(f"📡 Using manual panel configuration")
    else:
        parser.error("Either --panel or all manual options must be provided")

    key = asyncio.run(create_key(args.router, panel_config, args.email, args.dry_run))

    if key:
        print(f"\n🔑 VLESS KEY:")
        print(key)
        print(f"\n✅ Key ready for router: {args.router}")
        return 0
    else:
        print(f"\n❌ Failed to create key")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

---

## 20. Тулз: Добавление клиента на Fin3 (add_fin3_client.sh)

**Назначение:** Быстрое добавление клиента на Fin3 (третья Финляндия) с лимитами 365д/1TB.

**Использование:**
```bash
./add_fin3_client.sh <router_name> <uuid>
# Пример: ./add_fin3_client.sh TR56-99 a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Параметры Fin3:**
- Панель: `https://144.31.66.115:5050/5050`
- Inbound ID: 3
- Relay: `5.35.84.151:4191`
- PBK: `XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw`
- SID: `932e706c`
- SNI: `www.apple.com`

**Полный код скрипта (add_fin3_client.sh):**

```bash
#!/bin/bash
# Быстрое добавление клиента на Fin3 с лимитами 365д/1TB
# Использование: ./add_fin3_client.sh <router_name> <uuid>

ROUTER_NAME="${1:-}"
UUID="${2:-}"

if [ -z "$ROUTER_NAME" ] || [ -z "$UUID" ]; then
    echo "Использование: $0 <router_name> <uuid>"
    echo "Пример: $0 TR56-99 a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    exit 1
fi

# Fin3 параметры
PANEL_URL="https://144.31.66.115:5050/5050"
INBOUND_ID=3
RELAY_IP="5.35.84.151"
RELAY_PORT=4191
PBK="XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw"
SID="932e706c"
SNI="www.apple.com"

# Лимиты: 365 дней + 1 TB
ONE_YEAR_MS=$(($(date +%s) + 365 * 24 * 60 * 60))000
ONE_TB_BYTES=1099511627776

EMAIL="${ROUTER_NAME}_Fin3"

echo "=== Добавление клиента на Fin3 ==="
echo "Роутер: $ROUTER_NAME"
echo "UUID: $UUID"
echo "Email: $EMAIL"
echo "Лимиты: 365 дней / 1 TB"
echo ""

# Создаем payload
SETTINGS=$(cat <<EOF
{"clients":[{"id":"$UUID","email":"$EMAIL","limitIp":0,"enable":true,"expiryTime":$ONE_YEAR_MS,"totalGB":$ONE_TB_BYTES,"tgId":"","subId":"","comment":""}]}
EOF
)

# Логин и получение куки
echo "Логин в панель..."
LOGIN_RESP=$(curl -sk -X POST "$PANEL_URL/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"ad","password":"56"}' \
    -c /tmp/fin3_cookies.txt 2>/dev/null)

if [ ! -f /tmp/fin3_cookies.txt ] || ! grep -q "3x-ui" /tmp/fin3_cookies.txt 2>/dev/null; then
    echo "❌ Ошибка логина"
    exit 1
fi

echo "✅ Логин успешен"

# Проверяем существует ли клиент
echo "Проверка существующего клиента..."
EXISTING=$(curl -sk -b /tmp/fin3_cookies.txt "$PANEL_URL/panel/api/inbounds/get/$INBOUND_ID" 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); clients=json.loads(d.get('obj',{}).get('settings','{}')).get('clients',[]); print([c.get('email') for c in clients if c.get('email') == '$EMAIL'])" 2>/dev/null)

if echo "$EXISTING" | grep -q "$EMAIL"; then
    echo "⚠️ Клиент $EMAIL уже существует"
    echo ""
    echo "=== Готовый ключ ==="
    echo "vless://${UUID}@${RELAY_IP}:${RELAY_PORT}?type=grpc&security=reality&mode=gun&serviceName=&pbk=${PBK}&sid=${SID}&sni=${SNI}&fp=chrome&spx=%2F#${EMAIL}"
    exit 0
fi

# Добавляем клиента
echo "Добавление клиента..."
ADD_RESP=$(curl -sk -b /tmp/fin3_cookies.txt -X POST "$PANEL_URL/panel/api/inbounds/addClient" \
    -H "Content-Type: application/json" \
    -d "{\"id\":$INBOUND_ID,\"settings\":$(echo "$SETTINGS" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}" 2>/dev/null)

if echo "$ADD_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('SUCCESS' if d.get('success') else 'FAIL')" 2>/dev/null | grep -q "SUCCESS"; then
    echo "✅ Клиент добавлен успешно!"
    echo ""
    echo "=== Готовый ключ ==="
    echo "vless://${UUID}@${RELAY_IP}:${RELAY_PORT}?type=grpc&security=reality&mode=gun&serviceName=&pbk=${PBK}&sid=${SID}&sni=${SNI}&fp=chrome&spx=%2F#${EMAIL}"
    rm -f /tmp/fin3_cookies.txt
    exit 0
else
    echo "❌ Ошибка добавления клиента"
    echo "Ответ: $ADD_RESP"
    rm -f /tmp/fin3_cookies.txt
    exit 1
fi
```

---

## 21. Тулз: Проверка podkop на роутере (check-yt-on-router.sh)

**Назначение:** Проверка podkop на роутере — симулирует трафик на YouTube, Telegram, ChatGPT и др. Проверяет по обоим профилям (Main + YT).

**Использование:**
```bash
./check-yt-on-router.sh <IP роутера> [пароль]
# Пример: ./check-yt-on-router.sh 100.113.119.79
# Пример: ./check-yt-on-router.sh 100.87.253.107 56756789
```

**Что проверяет:**
1. Информацию о роутере (hostname, IP)
2. Профили Main и YT (сервер, статус)
3. Статус sing-box (запущен/остановлен)
4. Доступность сайтов через Main профиль (YouTube, Telegram, ChatGPT, Google, GitHub, Cloudflare)
5. Доступность YouTube через YT профиль (если включён)
6. Итоговую таблицу

**Полный код скрипта (check-yt-on-router.sh):**

```bash
#!/bin/bash
# check-yt-on-router.sh — проверка podkop на роутере
# Симулирует трафик на YouTube, Telegram, ChatGPT и др.
# Проверяет по обоим профилям (Main + YT)
#
# Использование:
#   ./check-yt-on-router.sh <IP роутера> [пароль]

set -euo pipefail

ROUTER_IP="${1:-}"
PASSWORD="${2:-56756789}"

if [ -z "$ROUTER_IP" ]; then
    echo "❌ Использование: $0 <IP роутера> [пароль]"
    exit 1
fi

SSH_OPTS="-o PreferredAuthentications=password -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o ConnectTimeout=10"

DOMAINS=(
    "youtube.com:YouTube"
    "telegram.org:Telegram"
    "chatgpt.com:ChatGPT"
    "google.com:Google"
    "github.com:GitHub"
    "cloudflare.com:Cloudflare"
)

echo "=========================================="
echo "🔍 ПРОВЕРКА PODKOP НА РОУТЕРЕ $ROUTER_IP"
echo "=========================================="
echo ""

# 1. Информация о роутере
HOSTNAME=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" 'cat /proc/sys/kernel/hostname 2>/dev/null || echo "unknown"' 2>/dev/null)
echo "📡 Роутер: $HOSTNAME ($ROUTER_IP)"
echo ""

# 2. Получаем оба профиля
MAIN_PROFILE=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" 'uci get podkop.main.proxy_string 2>/dev/null || echo ""' 2>/dev/null)
YT_PROFILE=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" 'uci show podkop 2>/dev/null | grep -E "^podkop\.(YT|yt)\.proxy_string=" | head -1' 2>/dev/null || echo "")
YT_ENABLED=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" 'uci get podkop.YT.enabled 2>/dev/null || uci get podkop.yt.enabled 2>/dev/null || echo "0"' 2>/dev/null || echo "0")

MAIN_LABEL=$(echo "$MAIN_PROFILE" | grep -oE '#.*' | tr -d '#' | head -c 40)
MAIN_SERVER=$(echo "$MAIN_PROFILE" | grep -oE '@[^:]+:[0-9]+' | head -1)
YT_LABEL=$(echo "$YT_PROFILE" | grep -oE '#.*' | tr -d '#' | head -c 40)
YT_SERVER=$(echo "$YT_PROFILE" | grep -oE '@[^:]+:[0-9]+' | head -1)

echo "━━━ ПРОФИЛИ ━━━"
echo "📌 Main: ${MAIN_LABEL:-не найден} (${MAIN_SERVER:---})"
echo "📺 YT:   ${YT_LABEL:-не найден} (${YT_SERVER:---})"
echo "   Статус: $([ "$YT_ENABLED" = "1" ] && echo '✅ включён' || echo '❌ выключен')"
echo ""

# 3. Проверяем, запущен ли podkop
PODKOP_RUNNING=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" 'pidof sing-box 2>/dev/null && echo "running" || echo "stopped"' 2>/dev/null)
echo "⚙️  Podkop (sing-box): $PODKOP_RUNNING"
echo ""

# 4. Проверка Main профиля
echo "━━━ ТЕСТ MAIN ПРОФИЛЯ ━━━"
echo ""
printf "  %-20s │ %-8s │ %-10s │ %s\n" "Сервис" "HTTP" "Время" "Статус"
printf "  %s\n" "─────────────────────┼──────────┼────────────┼────────────────────"

MAIN_ALL_OK=true
for DOMAIN_ENTRY in "${DOMAINS[@]}"; do
    DOMAIN="${DOMAIN_ENTRY%%:*}"
    LABEL="${DOMAIN_ENTRY##*:}"
    
    RESULT=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" \
        "curl -s --connect-timeout 8 --max-time 12 -o /dev/null -w '%{http_code}|%{time_total}' 'https://$DOMAIN' 2>/dev/null || echo '000|0'" 2>/dev/null)
    HTTP_CODE=$(echo "$RESULT" | cut -d'|' -f1)
    TIME_TOTAL=$(echo "$RESULT" | cut -d'|' -f2)
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "403" ]; then
        STATUS="✅ OK"
    elif [ "$HTTP_CODE" = "000" ]; then
        STATUS="❌ НЕТ"
        MAIN_ALL_OK=false
    else
        STATUS="⚠️ $HTTP_CODE"
        MAIN_ALL_OK=false
    fi
    
    printf "  %-20s │ %-8s │ %-10s │ %s\n" "$LABEL" "$HTTP_CODE" "${TIME_TOTAL}s" "$STATUS"
done

echo ""
echo "  Main профиль: $($MAIN_ALL_OK && echo '✅ ВСЁ РАБОТАЕТ' || echo '❌ ЕСТЬ ПРОБЛЕМЫ')"
echo ""

# 5. Проверка YT профиля
echo "━━━ ТЕСТ YT ПРОФИЛЯ ━━━"
echo ""

if [ "$YT_ENABLED" != "1" ] || [ -z "$YT_PROFILE" ]; then
    echo "  ⏭️  YT профиль выключен или не настроен — пропускаем"
else
    printf "  %-20s │ %-8s │ %-10s │ %s\n" "Сервис" "HTTP" "Время" "Статус"
    printf "  %s\n" "─────────────────────┼──────────┼────────────┼────────────────────"
    
    RESULT=$(sshpass -p "$PASSWORD" ssh $SSH_OPTS "root@$ROUTER_IP" \
        "curl -s --connect-timeout 8 --max-time 12 -o /dev/null -w '%{http_code}|%{time_total}' 'https://youtube.com' 2>/dev/null || echo '000|0'" 2>/dev/null)
    HTTP_CODE=$(echo "$RESULT" | cut -d'|' -f1)
    TIME_TOTAL=$(echo "$RESULT" | cut -d'|' -f2)
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        STATUS="✅ OK"
        YT_OK=true
    elif [ "$HTTP_CODE" = "000" ]; then
        STATUS="❌ НЕТ"
        YT_OK=false
    else
        STATUS="⚠️ $HTTP_CODE"
        YT_OK=false
    fi
    
    printf "  %-20s │ %-8s │ %-10s │ %s\n" "YouTube" "$HTTP_CODE" "${TIME_TOTAL}s" "$STATUS"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 ИТОГ ПРОВЕРКИ"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Main профиль: $($MAIN_ALL_OK && echo '✅ ВСЁ РАБОТАЕТ' || echo '❌ ЕСТЬ ПРОБЛЕМЫ')"
echo "  YT профиль:   $([ "$YT_ENABLED" != "1" ] && echo '⏭️  выключен' || ($YT_OK && echo '✅ РАБОТАЕТ' || echo '❌ НЕ РАБОТАЕТ'))"
echo ""
echo "  📡 Роутер: $HOSTNAME ($ROUTER_IP)"
echo "  ⚙️  Podkop: $PODKOP_RUNNING"
echo ""

if ! $MAIN_ALL_OK; then
    echo "  ❗ Main профиль не работает — проверь ключ"
    echo "     Возможно провайдер блокирует порт ${MAIN_SERVER##*:}"
fi

if [ "$YT_ENABLED" = "1" ] && ! $YT_OK; then
    echo "  ❗ YT профиль не работает — проверь ключ"
    echo "     Возможно провайдер блокирует порт ${YT_SERVER##*:}"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

---

## 22. Тулз: Tmux-бокс (tbox.sh)

**Назначение:** Запуск tmux-сессии "tbox" с Claude Code. Удобная обёртка для работы в tmux.

**Использование:**
```bash
bash ~/CLAUDECODE/tools/tbox.sh
# Или через алиас: tbox
```

**Полный код скрипта (tbox.sh):**

```bash
#!/bin/bash
# tbox.sh — запуск tmux-сессии "tbox" с Claude Code
# Использование: bash ~/CLAUDECODE/tools/tbox.sh
# Или через алиас: tbox

SESSION="tbox"

if [ -n "$TMUX" ]; then
  # Уже в tmux — просто запускаем claude
  exec claude "$@"
fi

# Создаём сессию если нет
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -n "chat" -x "$(tput cols)" -y "$(tput lines)"
  # Запускаем claude в окне chat
  tmux send-keys -t "$SESSION:chat" "claude" Enter
  tmux attach-session -t "$SESSION"
else
  # Сессия есть — просто присоединяемся
  tmux attach-session -t "$SESSION"
fi
```

---

## 23. Тулз: Ремонт 3 роутеров (t3.sh)

**Назначение:** Ремонт 3 роутеров в параллельных tmux-панелях. Запускает 3 агента Claude Code одновременно, каждый в своей панели.

**Использование:**
```bash
bash ~/CLAUDECODE/tools/t3.sh <ip1> <ip2> <ip3>
# Пример: bash ~/CLAUDECODE/tools/t3.sh 100.88.218.14 100.98.211.40 100.103.95.72
```

**Важно:** Должен быть запущен ВНУТРИ tmux-сессии (сначала `tbox`, потом `t3.sh`).

**Полный код скрипта (t3.sh):**

```bash
#!/bin/bash
# t3.sh — Ремонт 3 роутеров в параллельных tmux-панелях
# Использование: bash ~/CLAUDECODE/tools/t3.sh <ip1> <ip2> <ip3>
# Запускается из основного Claude (или вручную)
# Должен быть запущен ВНУТРИ tmux-сессии

set -e

R1="${1:?Нужен IP роутера 1}"
R2="${2:?Нужен IP роутера 2}"
R3="${3:?Нужен IP роутера 3}"

WINDOW_NAME="r:${R1##*.}|${R2##*.}|${R3##*.}"
PROMPT_SCRIPT="$HOME/CLAUDECODE/tools/gen-repair-prompt.sh"
CLAUDE_BIN="$HOME/.local/bin/claude"

if [ -z "$TMUX" ]; then
  echo "ОШИБКА: Нужно запустить внутри tmux. Сначала запусти: tbox"
  exit 1
fi

echo "🔧 Создаю окно агентов: $WINDOW_NAME"

# Создаём новое окно для агентов
tmux new-window -n "$WINDOW_NAME"
AGENTS_WIN="$WINDOW_NAME"

# Делим окно на 3 горизонтальные колонки
tmux split-window -t "$AGENTS_WIN" -h
tmux split-window -t "$AGENTS_WIN".2 -h
tmux select-layout -t "$AGENTS_WIN" even-horizontal

# Подписываем панели
tmux select-pane -t "$AGENTS_WIN".1 -T "🔧 $R1"
tmux select-pane -t "$AGENTS_WIN".2 -T "🔧 $R2"
tmux select-pane -t "$AGENTS_WIN".3 -T "🔧 $R3"

# Включаем показ заголовков панелей
tmux set-option -t "$AGENTS_WIN" pane-border-status top

# Генерируем промты и запускаем агентов
PROMPT1=$(bash "$PROMPT_SCRIPT" "$R1")
PROMPT2=$(bash "$PROMPT_SCRIPT" "$R2")
PROMPT3=$(bash "$PROMPT_SCRIPT" "$R3")

# Запускаем claude в каждой панели
TMPDIR=$(mktemp -d)
echo "$PROMPT1" > "$TMPDIR/p1.txt"
echo "$PROMPT2" > "$TMPDIR/p2.txt"
echo "$PROMPT3" > "$TMPDIR/p3.txt"

tmux send-keys -t "$AGENTS_WIN".1 \
  "$CLAUDE_BIN --dangerously-skip-permissions --output-format text -p \"\$(cat $TMPDIR/p1.txt)\" --add-dir \$HOME/CLAUDECODE 2>&1 | tee /tmp/agent-$R1.log" \
  Enter

tmux send-keys -t "$AGENTS_WIN".2 \
  "$CLAUDE_BIN --dangerously-skip-permissions --output-format text -p \"\$(cat $TMPDIR/p2.txt)\" --add-dir \$HOME/CLAUDECODE 2>&1 | tee /tmp/agent-$R2.log" \
  Enter

tmux send-keys -t "$AGENTS_WIN".3 \
  "$CLAUDE_BIN --dangerously-skip-permissions --output-format text -p \"\$(cat $TMPDIR/p3.txt)\" --add-dir \$HOME/CLAUDECODE 2>&1 | tee /tmp/agent-$R3.log" \
  Enter

echo "✅ Агенты запущены в окне: $WINDOW_NAME"
echo "   Ctrl+B → w  — список окон"
echo "   Ctrl+B → 2  — переключиться на агентов"
echo "   Логи: /tmp/agent-<IP>.log"

# Переключаемся на окно агентов
tmux select-window -t "$AGENTS_WIN"
```

---

## 🎯 Заключение

Этот файл содержит **полный набор скиллов и тулзов** для работы с OpenWrt роутерами, Podkop, Tailscale и VPN.

**Что нужно сделать другу:**
1. Положить этот файл в `~/CLAUDECODE/FRIEND_ONBOARDING.md`
2. Сказать Cline (DeepSeek): *"Прочитай FRIEND_ONBOARDING.md и следуй инструкциям"*
3. Cline сам разберётся: создаст папки `skills/` и `tools/`, скопирует туда скрипты, и будет использовать все скиллы и тулзы

**Что НЕ нужно передавать другу:**
- ❌ VLESS-ключи роутеров (папка `ключи/`)
- ❌ Пути к файлам прошивок (у друга свои)
- ❌ Личные токены и пароли

**Удачи, бро! 🚀**

