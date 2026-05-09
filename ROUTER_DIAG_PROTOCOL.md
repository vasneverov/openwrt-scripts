# 🚨 ПРОТОКОЛ ДИАГНОСТИКИ И РЕМОНТА РОУТЕРОВ
## Железный стандарт для всех моделей AI

**Читать в начале каждой сессии ремонта роутера.**
**Нарушение протокола = потеря доступа к роутеру.**

---

## Содержание

1. [Железные принципы](#1-железные-принципы)
2. [Фаза 0: Подготовка](#2-фаза-0-подготовка)
3. [Фаза 1: Первичная диагностика](#3-фаза-1-первичная-диагностика)
4. [Фаза 2: Глубокая диагностика](#4-фаза-2-глубокая-диагностика)
5. [Фаза 3: План лечения](#5-фаза-3-план-лечения)
6. [Фаза 4: Лечение](#6-фаза-4-лечение)
7. [Фаза 5: Финальная проверка](#7-фаза-5-финальная-проверка)
8. [Справочник: скрипты и инструменты](#8-справочник-скрипты-и-инструменты)
9. [Справочник: типовые проблемы и решения](#9-справочник-типовые-проблемы-и-решения)
10. [Справочник: серверы и порты](#10-справочник-серверы-и-порты)
11. [Справочник: роутеры и их конфигурации](#11-справочник-роутеры-и-их-конфигурации)

---

## 1. Железные принципы

### 1.1. Tailscale — спасать любой ценой
- **Tailscale — это единственный канал доступа к роутеру.** Потеря Tailscale = потеря роутера.
- `fw_mode=none` — иначе Tailscale убивает маршрутизацию
- `init.d tailscale DISABLED` — иначе при ребуте Tailscale стартует раньше сети
- `exclude_ntp=1` — иначе NTP ломает синхронизацию
- `rc.local` с tailscaled (sleep 40 для WR3000H/TR3000, sleep 25 для M3000)
- Watchdog в crontab (каждые 2-3 минуты проверяет tailscaled)
- `autoupdate=false` — никогда не обновляться автоматически
- **Перед любой перезагрузкой роутера проверить все 5 пунктов выше**

### 1.2. Сначала диагностика, потом план, потом лечение
- **НИКОГДА** не начинать лечение без полной диагностики
- Сначала собрать данные, потом показать пользователю план лечения
- Только после одобрения плана — приступать к лечению

### 1.3. Не перезагружать роутер без подтверждения
- Особенно если роутер за 1000 км от пользователя
- Перед ребутом проверить Tailscale-защиту (п. 1.1)

### 1.4. SSH к OpenWrt
- Всегда флаги: `-o PreferredAuthentications=password -o PubkeyAuthentication=no`
- Иначе sshpass падает exit 255

### 1.5. Если GitHub заблокирован — не паниковать
- Скрипты есть локально в `~/CLAUDECODE/tools/`
- Копировать через `cat | ssh` pipe
- .apk/.ipk пакеты есть локально в `~/CLAUDECODE/openwrt-packages/` и `~/CLAUDECODE/openwrt-apk-packages/`

### 1.6. OpenWrt 25.12 = apk (.apk), OpenWrt 24.x = opkg (.ipk)
- Проверить: `cat /etc/openwrt_release | grep DISTRIB_RELEASE`
- 25.12: `apk add пакет` (из репозитория)
- 24.x: `opkg install пакет.ipk`
- .ipk файлы НЕЛЬЗЯ использовать на 25.12

### 1.7. НИКОГДА не делать `tar -xzf data.tar.gz -C /` из ipk
- data.tar.gz содержит системные библиотеки (libc, libpthread и т.д.)
- Распаковка в корень перезаписывает их старыми версиями
- Это гарантированно ломает SSH и Tailscale

### 1.8. YT профиль — только заглавными
- `podkop.YT` — заглавные буквы (для M56/TR56/S78)
- Для Z56 (WR3000H) — строчные: `podkop.yt`
- Никогда не создавать неправильный регистр

### 1.9. Main профиль — не трогать без разрешения
- Без явного разрешения пользователя Main не менять
- Даже если ключ кажется нерабочим — сначала спросить

### 1.10. Ключи проверять перед установкой
- `python3 ~/CLAUDECODE/check_vless.py <ключ>`
- Только если `● READY` — ставить на роутер
- **НО:** `● READY` ≠ рабочий ключ. Настоящая проверка: `grep UUID /usr/local/x-ui/bin/config.json` на сервере

### 1.11. Ключи для нового роутера — брать с работающего
- При настройке нового роутера брать ключи с уже работающего роутера той же конфигурации
- Не изобретать новые ключи, не менять порты/pbk/sid/sni
- Менять только UUID (если нужен уникальный для каждого роутера)

### 1.12. Память между сессиями
- `deepsick_memory.md` — читать первым делом при старте
- `memory-lessons/` — уроки по каждому ремонту
- `ключи/vless_keys_all.md` — мастер-файл всех ключей
- После каждого ремонта обновлять все три файла

---

## 2. Фаза 0: Подготовка

### 2.1. Собрать информацию о роутере
```bash
# Известные роутеры (см. Справочник роутеров):
# - z56-08 (Сочи, 100.79.40.126) — TR5608, OpenWrt 25.12
# - tr56-09 (Жуковский, 100.116.130.9) — TR5609
# - tr56-06 (100.113.119.79) — TR5606
# - tr30-06 (100.116.14.50) — TR3006
# - z56-84 (Казань) — Z5684
# - z56-117 (Гомель) — Z56117
# - z56-119 (100.116.242.113) — Z56119
# - z56-54 (VasyaOnline_54, 100.102.103.55) — Z5654
# - s78-40 (100.118.37.35) — S7840
# - s78-44 (100.85.102.22) — S7844
```

### 2.2. Проверить доступность
```bash
# Tailscale ping
tailscale ping --c 3 <TAILSCALE_IP>

# SSH
sshpass -p '<PASSWORD>' ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@<TAILSCALE_IP> "echo ALIVE"
```

### 2.3. Прочитать уроки по этому роутеру
```bash
# Ищем файлы уроков по имени роутера
ls ~/CLAUDECODE/memory-lessons/ | grep <router_name>
```

---

## 3. Фаза 1: Первичная диагностика

Запустить на роутере **ОДНИМ SSH-запросом**:

```bash
sshpass -p '<PASSWORD>' ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@<TAILSCALE_IP> "

echo '=== 1. СИСТЕМА ==='
cat /etc/openwrt_release | grep DISTRIB_RELEASE
uptime
df -h / | tail -1
free -m | grep Mem

echo ''
echo '=== 2. TAILSCALE ==='
tailscale status --self | head -3
tailscale version
uci get tailscale.settings.fw_mode 2>/dev/null || echo 'fw_mode: not set'
/etc/init.d/tailscale enabled && echo 'init.d: ENABLED' || echo 'init.d: DISABLED'
grep tailscaled /etc/rc.local 2>/dev/null || echo 'rc.local: no tailscaled'
crontab -l | grep -i tailscale || echo 'watchdog: not found'
uci get podkop.settings.exclude_ntp 2>/dev/null || echo 'exclude_ntp: not set'

echo ''
echo '=== 3. SING-BOX ==='
pgrep -a sing-box
sing-box version 2>/dev/null | head -1

echo ''
echo '=== 4. PODKOP ==='
/etc/init.d/podkop enabled && echo 'init.d: ENABLED' || echo 'init.d: DISABLED'
uci show podkop.settings 2>/dev/null | grep -E 'dns_type|dns_server|download_lists|exclude_ntp|update_interval|log_level'
echo '--- profiles ---'
uci show podkop | grep '=section' | grep -v 'settings'
echo '--- main community_lists ---'
uci show podkop.main.community_lists 2>/dev/null
echo '--- YT community_lists ---'
uci show podkop.YT.community_lists 2>/dev/null || uci show podkop.yt.community_lists 2>/dev/null || echo 'YT: not found'

echo ''
echo '=== 5. ПРОВЕРКА IP ==='
echo '--- 2ip.ru ---'
curl -s --connect-timeout 5 --max-time 10 https://2ip.ru | head -3
echo '--- myip.ipip.net ---'
curl -s --connect-timeout 5 --max-time 10 https://myip.ipip.net
echo '--- ipinfo.io ---'
curl -s --connect-timeout 5 --max-time 10 https://ipinfo.io/json 2>/dev/null | grep -E '\"ip\"|\"country\"|\"city\"'

echo ''
echo '=== 6. ТЕСТЫ САЙТОВ ==='
for url in google.com youtube.com telegram.org facebook.com instagram.com rutracker.org tiktok.com; do
  printf '%-15s %3s %s\n' \"\$url\" \
    \"\$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 https://\$url 2>/dev/null)\" \
    \"\$(curl -s -o /dev/null -w '%{remote_ip}' --max-time 8 https://\$url 2>/dev/null)\"
done

echo ''
echo '=== 7. NFTABLES (podkop) ==='
nft list ruleset | grep -c 'podkop'
nft list chain inet PodkopTable mangle 2>/dev/null | head -20
nft list chain inet fw4 mangle_forward 2>/dev/null | grep 'podkop-fw4-fix' || echo 'podkop-fw4-fix: not found'

echo ''
echo '=== 8. ЛОГИ PODKOP (последние 20) ==='
logread -e podkop | tail -20

echo ''
echo '=== 9. /etc/hosts ==='
cat /etc/hosts

echo ''
echo '=== 10. ПРОВЕРКА СКРИПТОВ ==='
for script in rescue_generic.sh podkop-fw4-fix.sh podkop-fix-lists.sh; do
  [ -f /root/\$script ] && echo \"✅ \$script\" || echo \"❌ \$script\"
done
"
```

### 3.1. Интерпретация результатов

| Что смотрим | Норма | Проблема |
|-------------|-------|----------|
| **2ip.ru / myip.ipip.net** | Не Россия (Польша, Чехия, Италия, Финляндия) | Россия = podkop не работает |
| **ipinfo.io** | Россия (185.15.62.83) — это нормально | Если показывает Россия — не страшно, это не в списках |
| **YouTube** | 301 (FakeIP 198.18.0.x) | 000 = не работает |
| **Telegram** | 200 (FakeIP 198.18.0.x) | 000 = не работает |
| **Google** | 301 (реальный IP, не 198.18.0.x) | Если Google в FakeIP — проблема |
| **nftables podkop** | > 0 цепочек | 0 = podkop не создал правила |
| **fw4 mangle_forward** | Есть podkop-fw4-fix правила | Нет = forwarded трафик не маркируется |
| **sing-box** | RUNNING | Не запущен |
| **Tailscale** | Online, fw_mode=none, init.d DISABLED | Любое отклонение = риск потери доступа |
| **/etc/hosts** | Есть записи raw.githubusercontent.com | Нет = GitHub CDN может блокироваться |

---

## 4. Фаза 2: Глубокая диагностика

Если первичная диагностика выявила проблемы — углубиться.

### 4.1. Проверка forwarded трафика (ключевой тест)
```bash
# Если счётчики в PodkopTable mangle = 0, а трафик не идёт через прокси
nft list chain inet PodkopTable mangle 2>/dev/null | head -30
# Если счётчики prerouting = 0 — трафик не доходит до podkop
# Нужен podkop-fw4-fix.sh
```

### 4.2. Проверка GitHub CDN
```bash
# Проверить все 4 IP Fastly CDN
for ip in 185.199.108.133 185.199.109.133 185.199.110.133 185.199.111.133; do
  curl -sL --connect-timeout 5 --max-time 10 --resolve "raw.githubusercontent.com:443:$ip" \
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Subnets/IPv4/meta.lst" \
    -o /dev/null -w "$ip: HTTP %{http_code} (%{time_total}s)\n"
done
# Если 2 из 4 не работают — нужен podkop-fix-lists.sh
```

### 4.3. Проверка лимита open files (sing-box)
```bash
cat /proc/$(pgrep sing-box)/limits | grep "open files"
# Норма: 65536
# Проблема: 4096 (дефолт OpenWrt)
# Лечение: добавить procd_set_param limits "nofile=65536 65536" в /etc/init.d/sing-box
```

### 4.4. Проверка доступности серверов
```bash
# Проверить relay серверы
for port in 80 443 5050 5223 5228 5323 5328 8853 9443 465 993 2090 4191; do
  curl -sL -o /dev/null -w "bMSK:$port HTTP %{http_code} (%{time_total}s)\n" \
    --connect-timeout 5 --max-time 10 "https://159.194.198.172:$port" 2>/dev/null
done
```

### 4.5. Проверка конфига podkop на ошибки
```bash
# Проверить download_detour
grep download_detour /etc/sing-box/config.json 2>/dev/null
# Если есть "download_detour": "-out" — sing-box упадёт с FATAL
# Лечение: download_lists_via_proxy=0

# Проверить russia_inside
uci show podkop.main.community_lists 2>/dev/null | grep russia_inside
# Если есть — удалить
```

---

## 5. Фаза 3: План лечения

### 5.1. Составить план на основе диагностики

После сбора всей информации — **показать пользователю план лечения**.

Формат плана:

```markdown
## План лечения: <ROUTER_NAME> (<TAILSCALE_IP>)

### Текущее состояние
- **IP:** <страна/город>
- **YouTube:** <работает/не работает>
- **Telegram:** <работает/не работает>
- **Tailscale:** <стабилен/риск>
- **Podkop:** <работает/не работает>
- **fw4-fix:** <установлен/не установлен>
- **GitHub CDN:** <работает/блокируется>

### Проблемы
1. ...
2. ...

### План действий
1. [ ] Установить podkop-fix-lists.sh (если GitHub CDN блокируется)
2. [ ] Установить podkop-fw4-fix.sh (если forwarded трафик не маркируется)
3. [ ] Удалить YT профиль, добавить youtube в main (если YT не работает)
4. [ ] Исправить лимит open files (если too many open files)
5. [ ] Перезапустить podkop
6. [ ] Финальная проверка

### Риски
- <описать риски, если есть>
```

### 5.2. Дождаться одобрения пользователя
**НЕ НАЧИНАТЬ ЛЕЧЕНИЕ БЕЗ ОДОБРЕНИЯ ПОЛЬЗОВАТЕЛЯ.**

---

## 6. Фаза 4: Лечение

### 6.1. Спасительный скрипт (rescue_generic.sh)
**Применять на каждом новом роутере в первую очередь.**

```bash
# Если скрипта нет на роутере — скопировать с компа
cat ~/CLAUDECODE/tools/rescue_generic.sh | sshpass -p '<PASSWORD>' ssh ... \
  "cat > /root/rescue_generic.sh && chmod +x /root/rescue_generic.sh"

# Запустить
ssh ... "sh /root/rescue_generic.sh"
```

Что делает:
- Устанавливает `fw_mode=none`
- Отключает `init.d tailscale`
- Добавляет `rc.local` с tailscaled
- Устанавливает watchdog в crontab (каждые 2 мин)
- Устанавливает `exclude_ntp=1` в podkop

### 6.2. podkop-fix-lists.sh (GitHub CDN блокировка)
**Если провайдер блокирует часть IP Fastly CDN.**

```bash
# Скопировать
cat ~/CLAUDECODE/tools/podkop-fix-lists.sh | sshpass ... \
  "cat > /root/podkop-fix-lists.sh && chmod +x /root/podkop-fix-lists.sh"

# Запустить
ssh ... "sh /root/podkop-fix-lists.sh"

# Добавить в cron
ssh ... "echo '0 3 * * * /bin/sh /root/podkop-fix-lists.sh --cron' >> /etc/crontabs/root"
```

### 6.3. podkop-fw4-fix.sh (forwarded трафик)
**Если podkop не маркирует forwarded трафик (клиенты за роутером).**

```bash
# Скопировать
cat ~/CLAUDECODE/tools/podkop-fw4-fix.sh | sshpass ... \
  "cat > /root/podkop-fw4-fix.sh && chmod +x /root/podkop-fw4-fix.sh"

# Установить
ssh ... "/root/podkop-fw4-fix.sh install"
```

### 6.4. Исправление лимита open files
**Если в логах sing-box "too many open files".**

```bash
ssh ... "
# Добавить лимит в init.d скрипт
sed -i '/procd_set_param stdout/i procd_set_param limits \"nofile=65536 65536\"' /etc/init.d/sing-box
/etc/init.d/sing-box restart
"
```

### 6.5. Удаление YT профиля (если нужно)
```bash
ssh ... "
uci delete podkop.YT 2>/dev/null
uci add_list podkop.main.community_lists='youtube'
uci commit podkop
/etc/init.d/podkop restart
"
```

### 6.6. Перезапуск podkop
```bash
ssh ... "/etc/init.d/podkop restart"
# Подождать 30-40 секунд пока загрузятся списки
```

### 6.7. Обновление fw4 после перезапуска podkop
```bash
ssh ... "/root/podkop-fw4-fix.sh update"
```

---

## 7. Фаза 5: Финальная проверка

Запустить ту же диагностику, что в Фазе 1, и убедиться что:

- [ ] **2ip.ru** — не Россия ✅
- [ ] **myip.ipip.net** — не Россия ✅
- [ ] **YouTube** — 301 (FakeIP 198.18.0.x) ✅
- [ ] **Telegram** — 200 (FakeIP 198.18.0.x) ✅
- [ ] **Google** — 301 (реальный IP) ✅
- [ ] **Facebook/Instagram** — 301 (FakeIP) ✅
- [ ] **TikTok** — 301 (FakeIP) ✅
- [ ] **Rutracker** — 200 (FakeIP) ✅
- [ ] **nftables PodkopTable** — счётчики > 0 ✅
- [ ] **fw4 mangle_forward** — podkop-fw4-fix правила есть ✅
- [ ] **sing-box** — RUNNING ✅
- [ ] **Tailscale** — Online, fw_mode=none, init.d DISABLED ✅
- [ ] **/etc/hosts** — записи raw.githubusercontent.com ✅
- [ ] **Логи podkop** — ✅ Lists update completed successfully ✅

---

## 8. Справочник: скрипты и инструменты

### 8.1. Локальные скрипты (на компе)
| Скрипт | Путь | Назначение |
|--------|------|------------|
| rescue_generic.sh | `~/CLAUDECODE/tools/rescue_generic.sh` | Спасительный скрипт (Tailscale, podkop) |
| podkop-fix-lists.sh | `~/CLAUDECODE/tools/podkop-fix-lists.sh` | Чинит блокировку GitHub CDN |
| podkop-fw4-fix.sh | `~/CLAUDECODE/tools/podkop-fw4-fix.sh` | Чинит forwarded трафик на OpenWrt 25.12 |
| check_vless.py | `~/CLAUDECODE/check_vless.py` | Проверка VLESS ключей |
| vless_key.py | `~/CLAUDECODE/vless_key.py` | Генерация VLESS ключей |
| fix_keys_and_restart.py | `~/CLAUDECODE/fix_keys_and_restart.py` | Массовое исправление ключей |
| flash-router.sh | `~/CLAUDECODE/flash-router.sh` | Прошивка роутера |
| tmux-router-repair.sh | `~/CLAUDECODE/tmux-router-repair.sh` | Сессия tmux для ремонта |

### 8.2. Пакеты для установки
| Пакет | Путь | Для какой версии |
|-------|------|------------------|
| podkop-0.7.14-r1.apk | `~/CLAUDECODE/openwrt-apk-packages/` | OpenWrt 25.12 |
| luci-app-podkop-0.7.14-r1.apk | `~/CLAUDECODE/openwrt-apk-packages/` | OpenWrt 25.12 |
| luci-i18n-podkop-ru-0.7.14.apk | `~/CLAUDECODE/openwrt-apk-packages/` | OpenWrt 25.12 |
| sing-box-tiny_1.12.22-r1.apk | `~/CLAUDECODE/openwrt-apk-packages/` | OpenWrt 25.12 |
| podkop-v0.7.14-r1-all.ipk | `~/CLAUDECODE/openwrt-packages/` | OpenWrt 24.x |
| luci-app-podkop-v0.7.14-r1-all.ipk | `~/CLAUDECODE/openwrt-packages/` | OpenWrt 24.x |
| sing-box-tiny_1.12.22-r1.ipk | `~/CLAUDECODE/openwrt-packages/` | OpenWrt 24.x |

### 8.3. Списки podkop (community_lists)
**Для Main (20 списков, порядок важен):**
```
telegram, meta, geoblock, block, porn, news, anime, discord, twitter,
hdrezka, tiktok, cloudflare, google_ai, google_play, hodca, roblox,
hetzner, ovh, digitalocean, cloudfront
```

**Для YT (1 список):**
```
youtube
```

### 8.4. Как копировать файлы на роутер если GitHub заблокирован
```bash
# Текстовые скрипты — через cat pipe
cat ~/CLAUDECODE/tools/podkop-fix-lists.sh | sshpass -p '<PASS>' ssh ... "cat > /root/podkop-fix-lists.sh && chmod +x /root/podkop-fix-lists.sh"

# .apk/.ipk файлы — через scp -O
sshpass -p '<PASS>' scp -O ~/CLAUDECODE/openwrt-apk-packages/podkop-0.7.14-r1.apk root@<IP>:/tmp/
```

---

## 9. Справочник: типовые проблемы и решения

### 9.1. Podkop не работает (показывает Россию)

| Симптом | Причина | Решение |
|---------|---------|---------|
| podkop status = not running | Нормально для OpenWrt 25.12 | Проверить sing-box |
| nftables PodkopTable пустая | Podkop не создал правила | `/etc/init.d/podkop restart` |
| Счётчики mangle = 0 | Трафик не доходит до podkop | Установить podkop-fw4-fix.sh |
| fw4 mangle_forward нет правил | Forwarded трафик не маркируется | Установить podkop-fw4-fix.sh |
| После перезапуска podkop счётчики 0 | Нужно обновить fw4 | `/root/podkop-fw4-fix.sh update` |

### 9.2. GitHub CDN блокируется

| Симптом | Причина | Решение |
|---------|---------|---------|
| В логах podkop: "Attempt X/3 to download ... failed" | Провайдер блокирует часть IP Fastly CDN | Установить podkop-fix-lists.sh |
| wget зависает на raw.githubusercontent.com | DNS возвращает заблокированные IP | Добавить рабочие IP в /etc/hosts |
| curl с --resolve показывает 2 из 4 IP работают | Стандартная блокировка провайдера | podkop-fix-lists.sh решит |

### 9.3. Sing-box падает

| Симптом | Причина | Решение |
|---------|---------|---------|
| FATAL: download detour not found: -out | `download_lists_via_proxy=1` | Поставить `download_lists_via_proxy=0` |
| too many open files | Лимит 4096 исчерпан | Добавить `procd_set_param limits "nofile=65536 65536"` |
| FATAL: User already exists | Дубликаты клиентов в sqlite | Удалить дубликаты через sqlite |

### 9.4. YouTube не работает

| Симптом | Причина | Решение |
|---------|---------|---------|
| HTTP 000 на youtube.com | YT профиль не настроен | Удалить YT, добавить youtube в main |
| HTTP 000, порт сервера недоступен | Порт заблокирован firewall хостера | Использовать другой порт |
| HTTP 000, сервер отвечает | Неправильный ключ | Проверить UUID на сервере |

### 9.5. Tailscale нестабилен

| Симптом | Причина | Решение |
|---------|---------|---------|
| Точка зелёная, но SSH падает через 5 сек | init.d tailscale ENABLED | Отключить, настроить rc.local |
| После ребута Tailscale не поднялся | Нет rc.local или watchdog | Установить rescue_generic.sh |
| Tailscale убивает маршрутизацию | fw_mode не none | `tailscale set --fw-mode=none` |

### 9.6. После перезагрузки роутера всё сломалось

**Проверить:**
1. Tailscale поднялся? `tailscale status`
2. Podkop запущен? `/etc/init.d/podkop restart`
3. fw4 обновлён? `/root/podkop-fw4-fix.sh update`
4. Списки загрузились? Подождать 30-40 сек

---

## 10. Справочник: серверы и порты

### 10.1. Relay серверы

| Сервер | IP | Назначение |
|--------|----|------------|
| **bMSK** (Москва, Beget) | 159.194.198.172 | Основной relay, YT direct |
| **bSPB** (Питер) | 5.35.84.151 | Relay на Европу, панель x-ui |

### 10.2. Порты на bMSK

| Порт | Назначение | Статус |
|------|------------|--------|
| 80 | HTTP | ✅ Открыт |
| 443 | HTTPS | ✅ Открыт |
| 465 | SMTP SSL (YT direct) | ✅ Открыт |
| 993 | IMAPS (YT direct) | ✅ Открыт |
| 5050 | Панель x-ui | ✅ Открыт |
| 5223 | Relay PL6 | ✅ Открыт |
| 5228 | Relay PL6 | ✅ Открыт |
| 5323 | Relay PL6 | ✅ Открыт |
| 5328 | Relay PL6 | ✅ Открыт |
| 8853 | YT direct (старый) | ✅ Открыт |
| 9443 | Relay PL6 | ✅ Открыт |
| 2090 | ❌ Заблокирован хостерем | ❌ |

### 10.3. Выходные IP relay

| Relay | Выходной IP | Страна |
|-------|-------------|--------|
| PL6 (через bMSK:5223) | 91.92.46.152 | 🇵🇱 Польша |
| PL5 (через bSPB) | 82.38.66.75 | 🇬🇧 Великобритания |
| Fin3 (через bSPB:4191) | 144.31.66.115 | 🇫🇮 Финляндия |
| Italy (через bSPB:2090) | 151.243.198.86 | 🇮🇹 Италия |
| bMSK direct (465/8853) | 159.194.198.172 | 🇷🇺 Россия |

---

## 11. Справочник: роутеры и их конфигурации

### 11.1. Активные роутеры

| Имя | Tailscale IP | Модель | OpenWrt | Пароль | Конфигурация |
|-----|-------------|--------|---------|--------|-------------|
| **z56-08** (Сочи) | 100.79.40.126 | TR5608 | 25.12 | 56756789 | bMSK:9443→PL6 (Main) |
| **tr56-09** (Жуковский) | 100.116.130.9 | TR5609 | 25.12 | 56756789 | bMSK→PL6 |
| **tr56-06** | 100.113.119.79 | TR5606 | 25.12 | 56756789 | bSPB:2090→Italy (Main), bMSK:8853 (YT) |
| **tr30-06** | 100.116.14.50 | TR3006 | 25.12 | 56756789 | bMSK→PL6 |
| **z56-84** (Казань) | — | Z5684 | 25.12 | 56756789 | bMSK:5223→Fin4 (Main), bMSK:465 (YT) |
| **z56-117** (Гомель) | 100.87.253.107 | WR3000H | 25.12 | 56756789 | bSPB:2090→Italy (Main), bMSK:8853 (YT) |
| **z56-119** | 100.116.242.113 | — | 25.12 | 56756789 | Ключи от wbr-03 |
| **z56-54** (VasyaOnline_54) | 100.102.103.55 | — | — | 56756789 | ❌ Нет доступа |
| **s78-40** | 100.118.37.35 | WR3000S | 24.x | 56756789 | bMSK→PL6 (Main) |
| **s78-44** | 100.85.102.22 | WR3000S | 24.x | ne78va | bSPB (Main) |

### 11.2. Типовые конфигурации

**Стандартная (bMSK→PL6):**
- Main: `vless://UUID@159