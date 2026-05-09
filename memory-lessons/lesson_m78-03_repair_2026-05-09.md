# Урок: M78-03 (Вера Гришина) — ремонт 09.05.2026

**Роутер:** M78-03 (100.100.82.6)
**Версия podkop:** v0.7.10
**Версия OpenWrt:** 24.10 (M78)

## Диагностика
- Подкоп **не запущен** (not running)
- Версия старая v0.7.10 (последняя v0.7.14)
- Community lists не скачаны (0 файлов)
- Есть Calls профиль (Telegram/WhatsApp) и YT профиль
- exclude_ntp = 0
- fw_mode не задан
- Tailscale через rc.local (старый способ)
- Нет watchdog'а для podkop

## Что сделано
1. **Проверен main ключ** через check_vless — ● READY, через релей (cz.8bit.ca)
2. **Удалён Calls профиль** — Telegram/WhatsApp не нужны в отдельном профиле
3. **Удалён YT профиль** — youtube добавлен в main community_lists
4. **exclude_ntp → 1**
5. **fw_mode → none**
6. **Community lists** — 20 списков (без roblox, т.к. v0.7.10)
7. **Порядок списков:** telegram, meta, youtube — первые три (правило #29)

## Важно
- **Версия podkop влияет на количество списков:** v0.7.10 — 20 (без roblox), v0.7.14 — 21 (с roblox)
- **Перед установкой списков — проверить версию:** `opkg list-installed | grep podkop`
- **Если поставить roblox на v0.7.10** — podkop падает с `fatal: Invalid service`

## Результат
- Подкоп **running**
- Google — HTTP 200 ✅
- YouTube — HTTP 200 ✅
- Один main профиль, всё чисто
