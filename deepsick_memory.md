# Памятка DeepSeek (Вася)

## ⚠️ ЧИТАТЬ ПРИ СТАРТЕ КАЖДОЙ СЕССИИ:
1. **`IRON_RULES.md`** — железные правила (нарушение = поломка)
2. **`CLAUDE_00.md`** — полная инструкция по прошивке роутеров
3. **`memory-lessons/`** — последний урок (чтобы знать что делали в прошлый раз)
4. **`ключи/vless_keys_all.md`** — мастер-файл всех ключей

## О Васе
- Имя: Вася
- Возраст: 47 лет
- Общаемся на "ты", простыми словами
- Предпочитает вежливое общение без грубости

## Настройки общения
- Говорить простым языком, без сложных терминов
- Когда делаю что-то в файлах - рассказываю здесь, не открывая редактор
- Спрашиваю только в критических случаях
- Работаю в автономном режиме по возможности

## Текущая сессия (09.05.2026)
### Что сделали:
1. **007-ufa (100.99.195.91, Cudy WR3000E, Уфа)** — полный ремонт podkop
   - Удалили YT профиль, добавили youtube в main (порядок: telegram, meta, youtube...)
   - Установили podkop-fw4-fix (правила в inet fw4 mangle_forward)
   - Исправили лимит open files для sing-box (4096 → 65536)
   - Добавили /etc/hosts для raw.githubusercontent.com
   - Скопировали все 3 спасительных скрипта
   - Добавили cron для podkop-fix-lists.sh
   - **YouTube: 000 → 301 (FakeIP)** ✅
   - **2ip.ru** → 🇵🇱 Польша (91.92.46.229) ✅
2. **tr56-04-doc-dom (100.82.166.40, Cudy TR3000, Дом.ru СПб)** — полный ремонт podkop
   - Удалили YT профиль, добавили youtube в main (21 список)
   - Установили podkop-fw4-fix (правила в inet fw4 mangle_forward)
   - Исправили лимит open files для sing-box (4096 → 65536)
   - Добавили /etc/hosts для raw.githubusercontent.com
   - Скопировали все 3 спасительных скрипта
   - Добавили cron для podkop-fix-lists.sh
   - **YouTube: 000 → 301 (FakeIP)** ✅
   - **2ip.ru** → 🇵🇱 Польша (91.92.46.229) ✅
3. **z56-08 (100.79.40.126, Сочи)** — починили podkop на OpenWrt 25.12
   - Перезапустили podkop, загрузили списки (919 элементов)
   - Установили podkop-fw4-fix (правила inet fw4 mangle_forward)
   - **2ip.ru** → 🇵🇱 Польша (91.92.46.152) ✅
4. **z56-09 (100.116.130.9, tr56-09-maxim-bazhenov)** — установили podkop-fw4-fix
   - 864 элемента скопировано в fw4 mangle_forward
   - **2ip.ru** → 🇨🇿 Чехия (92.61.71.14) ✅
5. **e-008-tvoy-oblik (100.83.104.61, Cudy WR3000E)** — быстрый ремонт podkop
   - Tailscale уже настроен (fw_mode=none, init.d disabled, rc.local)
   - Удалили YT профиль, youtube в main (telegram, meta, youtube...)
   - Установили podkop-fw4-fix (4 правила в mangle_forward)
   - Исправили лимит open files (4096 → 65536)
   - Добавили /etc/hosts для GitHub CDN
   - Скопировали podkop-fw4-fix.sh и podkop-fix-lists.sh
   - Добавили cron для podkop-fix-lists.sh
   - **YouTube: 000 → 301 (FakeIP)** ✅
   - **2ip.ru** → 🇵🇱 Польша (91.92.46.229) ✅
6. **Создали три скрипта с правильными названиями:**
   - **Спасительный** (`rescue_generic.sh`) — стабилизация роутера, 3 watchdog'а
   - **Листовой** (`tools/podkop-fix-lists.sh`) — фикс блокировки GitHub CDN
   - **fw4-fix** (`tools/podkop-fw4-fix.sh`) — фикс forwarded трафика на OpenWrt 25.12+
7. **Обновили алгоритм диагностики** (`skills/podkop_diag_algo.md`)
8. **Создали памятку** (`skills/podkop_repair_guide.md`)



### Проблема OpenWrt 25.12 + podkop
- На OpenWrt 25.12 (fw4/nftables) таблица `inet PodkopTable` с `hook prerouting` **не видит forwarded трафик** (с клиентов WiFi/LAN)
- Видит только local трафик (с самого роутера через SSH)
- **Решение:** podkop-fw4-fix.sh — добавляет правила в `inet fw4 mangle_forward` (hook forward)
- **Симптом:** с роутера curl показывает нужную страну, с клиентов — Россия

### Уроки из ремонтов 09.05.2026
1. **YT профиль — всегда удалять, youtube добавлять в main.** Отдельный YT профиль с bSPB:8853 не работает, потому что bSPB часто падает. В main через bMSK:5323→PL5 YouTube работает стабильно.
2. **Провайдер Дом.ru блокирует прямые TCP-соединения** — даже 1.1.1.1:53 и 8.8.8.8:53 недоступны. Но podkop через прокси работает, потому что трафик идёт через sing-box туннель.
3. **Лимит open files 4096 — частая проблема.** После перезапуска sing-box с лимитом 65536 всё стабильно.
4. **После перезапуска podkop обязательно делать `podkop-fw4-fix.sh update`** — иначе fw4 mangle_forward остаётся со старыми сетами.
5. **Порядок лечения:** сначала конфиг (YT→main), потом скрипты, потом перезапуск, потом fw4 update. Не перезагружать роутер.
6. **fw4-fix нужен не только на OpenWrt 25.12, но и на 24.10.x** — проблема в nftables в целом, не только в новой версии.
7. **Если Tailscale уже настроен (fw_mode=none, init.d disabled, rc.local) — спасительный скрипт не нужен.** Достаточно только podkop-скриптов.
8. **Быстрый ремонт podkop (без Tailscale) занимает ~2 минуты:** скрипты → YT→main → fw4-fix → лимиты → /etc/hosts → cron → перезапуск → fw4 update.
9. **Порядок списков в main:** telegram, meta, youtube — первые три. Запомнить.
10. **Tailscale может падать при первом SSH-подключении** — если роутер только что перезагрузился. Нужно подождать или переподключиться.



### Спящие агенты (три скрипта, которые ставятся на роутер)
1. **Спасительный** — `rescue_generic.sh` (в корне репозитория)
   - Ставит: fw_mode=none, init.d disable, exclude_ntp=1, rc.local, firewall tailscale0 в LAN, 3 watchdog'а, crontab
   - Запуск: `cat rescue_generic.sh | ssh root@ROUTER_IP sh -s`
   - Оригинал на GitHub: `sh <(wget -O - https://raw.githubusercontent.com/vasneverov/openwrt-fix/main/fix-tailscale-openwrt.sh)`

2. **Листовой** — `tools/podkop-fix-lists.sh`
   - Чинит блокировку GitHub CDN (raw.githubusercontent.com)
   - Применяется когда в логах podkop `download failed`
   - Установка: `cat tools/podkop-fix-lists.sh | ssh root@ROUTER_IP "cat > /root/podkop-fix-lists.sh && chmod +x /root/podkop-fix-lists.sh"`
   - Добавить в crontab: `0 4 * * * /bin/sh /root/podkop-fix-lists.sh --cron`

3. **fw4-fix** — `tools/podkop-fw4-fix.sh`
   - Чинит forwarded трафик на OpenWrt 25.12+
   - Применяется когда с роутера работает, с клиентов нет
   - Установка: `cat tools/podkop-fw4-fix.sh | ssh root@ROUTER_IP "cat > /root/podkop-fw4-fix.sh && chmod +x /root/podkop-fw4-fix.sh"` затем `ssh root@ROUTER_IP "/root/podkop-fw4-fix.sh install"`

**Установка всех спящих агентов одной командой:**
```
for script in podkop-fw4-fix.sh podkop-fix-lists.sh; do
  cat tools/$script | ssh root@ROUTER_IP "cat > /root/$script && chmod +x /root/$script"
done
ssh root@ROUTER_IP "/root/podkop-fw4-fix.sh install"
ssh root@ROUTER_IP "(crontab -l 2>/dev/null; echo '0 4 * * * /bin/sh /root/podkop-fix-lists.sh --cron') | crontab -"
```


### Алгоритм диагностики (кратко)
1. Быстрая проверка (sing-box, Tailscale, маршрутизация, логи)
2. Если листы не качаются → листовой скрипт
3. Если sing-box не стартует → mixed_proxy=0
4. ФИНАЛЬНАЯ ПРОВЕРКА: проверить IP с роутера И с клиента
5. Если с клиента не работает → fw4-fix скрипт
6. Если роутер нестабилен → спасительный скрипт

### Файлы настроек:
- `/Users/vas/CLAUDECODE/.vscode/settings.json` - настройки Cline
- `/Users/vas/CLAUDECODE/deepsick_memory.md` — память между сессиями
- `/Users/vas/CLAUDECODE/memory-lessons/` — уроки по ремонтам
- `/Users/vas/CLAUDECODE/ключи/vless_keys_all.md` — мастер-файл всех ключей
- `/Users/vas/CLAUDECODE/skills/podkop_diag_algo.md` — алгоритм диагностики
- `/Users/vas/CLAUDECODE/skills/podkop_repair_guide.md` — памятка по ремонту
- `/Users/vas/CLAUDECODE/IRON_RULES.md` — железные правила

### Архитектура:
- Claude Code (отдельное приложение) - работает с Claude
- Cline (расширение VS Code) - работает с DeepSeek

## Проекты для работы
- VPN инфраструктура: сервера bMSK (159.194.198.172 — Москва) и bSPB (5.35.84.151 — Питер)
- X-UI панели: https://IP:5050/5050, логин ad/пароль 56
- SSH: root@IP, пароль Ujkjdf56#
- Fin4 (Польша 4): 45.155.55.198:5050, логин ad/пароль 56

## Задачи на будущее
- Сделать 10 ключей для 10 роутеров на низких портах (110, 143, 2086, 2087, 2095)
- Протестировать ключ TR30-25 на порту 465

## Важные решения
### Низкие порты 465 и 993 — РАБОТАЮТ (05.05.2026)
- **Порт 465** (SMTP SSL) — работает на bMSK для TR30-25
- **Порт 993** (IMAPS) — работает на bMSK для VasyaOnline YT и TR56-06
- **Порт 631** (IPP) — работает на bMSK

### Fin4 (Польша 4) — параметры
- IP: 45.155.55.198
- Inbound-4191 (ID:1): sid=`4b929012`, pbk=`HfbTqAITJraOSM3J+yHpedrv+lKKe41IkU5m+4yPbHI`
- Inbound-4192 (ID:2): sid=`ae2bfb99`
- Relay через bMSK:5223

### Железные правила (Iron Rules):
1. **YT профиль — всегда заглавными буквами** (`podkop.YT`, не `podkop.yt`)
2. **Main профиль — никогда не трогать** без явного разрешения
3. **Podkop не перезагружать** — только сохранить, пользователь сам перезагрузит
4. **Tailscale спасать любой ценой** — fw_mode=none, init.d disable, rc.local, watchdog

### Ключевые правила создания ключей:
1. REALITY ключи генерировать ТОЛЬКО через `/usr/local/x-ui/bin/xray x25519`
   - ❌ openssl даёт НЕВЕРНЫЕ ключи (xray падает с invalid "privateKey")
   - ✅ xray x25519 даёт правильные ключи
2. gRPC Reality: поле flow должно быть ПУСТЫМ
3. Перезапуск xray: `/usr/local/x-ui/x-ui.sh restart`
4. Проверка: `ss -tlnp | grep xray`
5. **Один UUID на оба профиля (YT + Main)** — удобно, меньше путаницы

### Доступные низкие порты на bMSK (свободны):
110 (POP3), 143 (IMAP), 2086, 2087, 2095 (Cloudflare)


---
*Этот файл создан для памяти между сессиями. При каждом новом вызове читать первым делом.*

