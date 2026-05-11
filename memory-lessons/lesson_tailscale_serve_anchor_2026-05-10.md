# Урок: Tailscale serve anchor — фиксация long-poll при первой авторизации

**Дата:** 2026-05-10
**Роутер:** tr-boss-00 (100.123.243.33)
**Проблема:** После `tailscale up --authkey=...` точка зелёная, но через 5-10 сек гаснет

## Суть

При первой авторизации Tailscale через pre-auth key, long-poll соединение с control plane может оборваться. Точка становится зелёной, но через несколько секунд гаснет.

**Решение:** `tailscale serve` — это не только проброс портов. Когда serve активен, Tailscale держит постоянное соединение с control plane (HTTPS-сертификат через Let's Encrypt, регистрация Funnel/Serve endpoint). Это **фиксирует long-poll** — точка не гаснет.

## Алгоритм (для flash_router_universal.md, шаг 7)

```bash
# 1. Авторизация через pre-auth key
tailscale up --accept-dns=false --accept-routes --authkey=tskey-auth-xxxxx

# 2. Сразу serve anchor (фиксирует long-poll)
tailscale serve --bg --tcp 80  tcp://localhost:80
tailscale serve --bg --tcp 443 tcp://localhost:443
tailscale serve --bg --tcp 22  tcp://localhost:22

# 3. Ждём зелёную точку (ping-цикл)
# tailscale status → ONLINE (100.x, статус "-")

# 4. Убираем serve (больше не нужен)
tailscale serve --tcp=80 off
tailscale serve --tcp=443 off
tailscale serve --tcp=22 off
```

## Почему это работает

`tailscale serve` создаёт:
- HTTPS-сертификат через Let's Encrypt (через controlplane.tailscale.com)
- Регистрирует Funnel/Serve endpoint в Tailscale cloud
- **Это заставляет long-poll держаться** — Tailscale постоянно держит соединение с control plane для serve

После того как точка зелёная и watchdog'ы установлены — serve не нужен. Watchdog'ы (ts-watchdog v3.1) не дают long-poll оборваться.

## Установка Tailscale

Вместо ручного добавления репозитория gunano — однострочный скрипт:
```bash
sh -c "$(wget -O- https://raw.githubusercontent.com/GuNanOvO/openwrt-tailscale/main/install_en.sh)" --persistentinstall
```
Скрипт сам определяет архитектуру и ставит правильную версию (толстую или UPX).

## Что изменилось в скиллах

1. **flash_router_universal.md** — Шаг 6: установка через gunano скрипт. Шаг 7: авторизация + serve anchor + убрать serve
2. **podkop_repair_guide.md** — Добавлены пункты 4 (установка) и 5 (serve anchor)
3. **ROUTER_DIAG_PROTOCOL.md** — Раздел 1.1: обновлены правила Tailscale
