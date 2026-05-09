# Урок: Полная диагностика и создание ключа для 19-ternovsky (Сочи)

> Дата: 2026-05-08
> Роутер: 19-ternovsky (100.88.218.14) — VasyaOnline_19, Xiaomi AX3000T
> OpenWrt: 24.10.1 | Podkop: v0.7.14 | Sing-box: 1.12.22 | Tailscale: 1.80.3

## Проблема
Роутер перестал работать после того, как podkop не мог скачать rule_set-ы с GitHub (raw.githubusercontent.com заблокирован в РФ). Sing-box падал, трафик не маркировался.

## Диагностика (алгоритм)

### Фаза 1 — Базовые проверки
1. **Tailscale** — проверить статус, IP в сети
2. **Podkop** — статус (running/not running)
3. **Sing-box** — запущен ли (ps | grep sing-box)
4. **nftables** — проверить счётчики в PodkopTable mangle (packets 0 = не работает)
5. **logread** — логи podkop и sing-box
6. **Провайдер** — определить по WAN IP (whois, ipinfo)
7. **Порты** — проверить какие порты блокирует провайдер (curl на разные порты сервера)

### Фаза 2 — Лечение
1. **download_lists_via_proxy=0** — чтобы sing-box не падал при загрузке списков
2. **/etc/hosts** — добавить рабочие IP для raw.githubusercontent.com (найти через nslookup или известные)
3. **podkop-fw4-fix.sh** — установить 4 правила mangle_forward для forwarded трафика
4. **podkop-fix-lists.sh** — скопировать в /root
5. **Watchdog** — добавить в cron (каждые 2 мин)

### Фаза 3 — Проверка IP и страны
5 сервисов для проверки внешнего IP:
1. **2ip.ru** — показывает IP через прокси
2. **myip.ipip.net** — показывает IP + страну + город + провайдера
3. **ipinfo.io/json** — JSON с IP, городом, регионом, страной, провайдером
4. **ifconfig.me** — показывает прямой IP (без прокси)
5. **ip-api.com/json** — JSON с IP, страной, городом, ISP, AS

### Фаза 4 — Тесты сайтов (7 сайтов)
Проверка с флагом `-L` (следовать редиректам):
- google.com — ✅ 200
- youtube.com — ✅ 200
- telegram.org — ✅ 200
- facebook.com — ✅ 200
- instagram.com — ✅ 200
- rutracker.org — ✅ 200
- tiktok.com — ✅ 200

### Фаза 5 — Анализ конфига
1. `uci show podkop` — полный конфиг
2. `cat /etc/config/podkop` — файл конфига
3. `cat /etc/sing-box/config.json` — конфиг sing-box
4. Расшифровать proxy_string: сервер, порт, pbk, sid, transport
5. Сверить pbk/sid со справочником SERVERS_RELAY_REFERENCE.md

### Фаза 6 — Создание нового ключа
1. Зайти на панель целевого сервера (CZ2: https://92.61.71.14:5050/5050/)
2. Найти inbound с нужным портом (8448) — ID 18
3. Сгенерировать новый UUID
4. Добавить клиента через API:
   ```
   POST /panel/api/inbounds/addClient
   {"id":18,"settings":"{\"clients\":[{\"id\":\"NEW_UUID\",\"email\":\"NAME_CZ2\",...}]}"}
   ```
5. Прописать новый ключ на роутере:
   - `uci set podkop.main.proxy_string='vless://...'`
   - `uci commit podkop`
   - `/etc/init.d/podkop restart`

## Структура подключения (для 19-ternovsky)
```
19-ternovsky (Сочи, провайдер Greenline Ltd)
    │
    └─ main (21 список: telegram, meta, youtube, geoblock, block, porn,
             news, anime, discord, twitter, hdrezka, tiktok, cloudflare,
             google_ai, google_play, hodca, roblox, hetzner, ovh,
             digitalocean, cloudfront)
           │
           ├─ bSPB:8448 (5.35.84.151, Санкт-Петербург, Beget)
           │     └─ DNAT → CZ2:8448 (92.61.71.14, Чехия, smartape.net)
           │
           └─ Выходной IP: 92.61.71.14 🇨🇿 Чехия
```

## Новый ключ
```
Сервер:     CZ2 (92.61.71.14)
Inbound:    ID 18, порт 8448
UUID:       c8adcc65-87df-4a49-89fa-12127503e67b
Email:      19-ternovsky_CZ2
pbk:        FyCxYT4Ku_RyR7r2dZYofYxcAOm5xJtgP-T_xjgVnCQ
sid:        dcaa
SNI:        www.apple.com
Transport:  gRPC + Reality + TLS
```

## Важные заметки
1. **19-ternovsky** — это НЕ TR5608. Это разные роутеры.
2. YT профиль удалён, YouTube добавлен 21-м списком в main — так проще и надёжнее.
3. При проверке сайтов использовать `-L` (follow redirects), иначе 301/302 будут показываться как ошибка.
4. fakeIP (198.18.0.0/15) — это нормально, так работает podkop/sing-box.
5. Для следующего раза: добавить в main списки `chatgpt`, `claude`, `ai` — чтобы AI-сервисы тоже шли через прокси.
