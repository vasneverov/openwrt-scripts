# NaiveProxy — памятка

## Что такое NaiveProxy
- Прокси-протокол на основе HTTPS (HTTP/2 + TLS)
- Маскируется под обычный HTTPS-трафик — DPI не может отличить от реального браузера
- Использует Chrome-стек (Chromium network stack) — полная эмуляция браузера
- Работает через Caddy с патчем forwardproxy (форк klzgrad)

## Чем лучше VLESS (3xUI)
- VLESS (Xray/3xUI) — собственный протокол, DPI в РФ научились его детектить
- NaiveProxy — это просто HTTPS, DPI не может его заблокировать не заблокировав весь HTTPS
- Не требует WebSocket, gRPC, фейковых доменов — всё уже замаскировано
- Единственный способ заблокировать — по IP или порту

## Архитектура
- Сервер: Caddy + forwardproxy (патч klzgrad)
- Клиент: NaiveProxy (нативный клиент) или любой HTTP/2 прокси-клиент
- Формат ключа: `https://username:password@domain:port`
- Настройка в клиенте: тип HTTPS, адрес, порт, пользователь, пароль, TLS включён

## Развёртывание на сервере PL6 (82.38.66.75)
- Сервер: PL6 (Польша)
- Домен: open.theredhat.su (ведёт на PL6)
- Порт: 443 (работает в РФ, в отличие от 52.23)
- Пароль: 56756789
- Работает в Docker, изолированно от 3xUI
- docker-compose.yml, Caddyfile, Dockerfile — на сервере в /root/naiveproxy/

## Бот @vasyaVPNbot
- Сервер бота: 82.38.66.75 (там же где PL6)
- ADMIN_ID: 50949302 (Василий Неверов)
- Токен: 7522740777:AAH97UDULbuevaw0vS0IDw3gb4wsuhODm5A
- Код бота: /opt/xui-bot/
- Файлы: main.py, database.py, handlers/start.py, handlers/naive.py, handlers/create_user.py и др.

## Проблема с Naive в боте
- Кнопка "🧅 Naive" была в ReplyKeyboardMarkup (кнопки в поле ввода)
- Telegram кэширует ReplyKeyboard — при нажатии на "🧅 Naive" бот отправляет Inline-кнопки, но Telegram не обновляет ReplyKeyboard
- Пользователь видит старые Reply-кнопки ("PL6", "Отмена") вместо Inline-кнопок
- **Решение:** убрать "🧅 Naive" из ReplyKeyboard, добавить как Inline-кнопку под сообщением после /start
- Файлы изменены: handlers/start.py (убрана кнопка, добавлена admin_inline_kb), handlers/naive.py (обработчик через callback_query вместо message)
- **НО:** после загрузки на сервер и перезапуска пользователь всё ещё видит старые кнопки — возможно Telegram кэширует клавиатуру на клиенте

## Relay через bMSK (Москва) — НАСТРОЕНО ✅
- **bMSK порт:** 5443 → PL6:443 (DNAT)
- **Сервер:** bMSK (159.194.198.172)
- **Цель:** PL6 (91.92.46.152:443) — NaiveProxy Caddy
- **DNS:** `open.theredhat.su → 159.194.198.172` (A-запись изменена)
- **Правила nftables на bMSK:**
  - FORWARD: ip daddr 91.92.46.152 tcp/udp dport 443 accept
  - PREROUTING: tcp/udp dport 5443 dnat to 91.92.46.152:443
  - POSTROUTING: ip daddr 91.92.46.152 tcp/udp dport 443 masquerade
- **Сохранено:** `/etc/nftables.d/99-naiveproxy.nft`
- **Проверка:** `curl https://open.theredhat.su:5443/` → HTTP 404 (Caddy ответил) ✅

## Формат ключа для клиента (через relay)
```
https://naive:56756789@open.theredhat.su:5443
```

## Пользователи Caddy на PL6
- `vasya56` / `56neverov` — старый пользователь (оставлен для совместимости)
- `naive` / `56756789` — пользователь для бота @vasyaVPNbot
- Оба работают через relay bMSK:5443 → PL6:443

## Что сделано с ботом
- [x] Убрана кнопка "🧅 Naive" из ReplyKeyboard (она не работала)
- [x] Добавлена `admin_inline_kb()` — Inline-кнопка "🧅 NaiveProxy" под сообщением
- [x] При `/start` показывается ReplyKeyboard + Inline-кнопка NaiveProxy
- [x] Добавлен хендлер для текста "🧅 Naive" (для старых кэшированных клавиатур)
- [x] Docker-образ пересобран и контейнер перезапущен
- [x] Код в контейнере проверен — всё на месте

## Рекомендации по портам для РФ
- 443 — работает (HTTPS)
- 80 — работает (HTTP)
- 8880 — работает (альтернативный HTTP)
- 8443 — работает (альтернативный HTTPS)
- 52.23 — НЕ работает (заблокирован провайдером)
- 2096 — может работать (Cloudflare)
- 2053 — может работать (Cloudflare)
