---
name: Сессия 26.04.2026 — failover, NL2→Italy, S78-44
description: Уроки сессии: экстренный failover для бандлов, замена NL2 на Italy, ремонт S78-44
date: 2026-04-26
type: feedback
critical: false
---

# Уроки сессии 26.04.2026

## Что сделано

1. **NL2 🇳🇱 → Italy 🇮🇹 в Bundle 1** — заменены три файла: bundle_rotate.py, server.py, create_user.py (xui-bot). Образ Docker пересобран.
2. **failover.py** — новый скрипт экстренного переключения бандлов, cron каждые 2 минуты. Telegram-уведомление при сбое.
3. **Фикс server.py** — `check_bundle_with_fallback()` теперь пишет в JSON при нахождении fallback.
4. **S78-44 (Cudy WR3000S v1, ne78va, 100.85.102.22)** — создан bSPB ключ, секция YT (uppercase), исправлены community_lists, удалена секция calls, exclude_ntp=1.

---

## Ключевые открытия

### 1. Мёртвое окно без failover — 57 минут
Cron rotate раз в час. Если сервер упал в 9:03 — клиент пишет "ничего не работает" до 10:00. Решение: отдельный failover.py (каждые 2 мин) + запись JSON в server.py при fallback. Итоговое мёртвое окно — 2 минуты.

**Архитектура трёх уровней защиты:**
- Уровень 1: `failover.py` cron каждые 2 мин — пишет JSON, шлёт Telegram
- Уровень 2: `server.py check_bundle_with_fallback()` — при каждом запросе клиента, пишет JSON
- Уровень 3: `bundle_rotate.py` — плановая ротация каждый час (про "сегодня Италия")

### 2. Italy в двух бандлах одновременно — безопасно
Italy теперь в B1 и B2. Порог `>= 2` в server.py корректно разделяет: B1-юзер имеет 4 B1-сервера (>= 2), Italy-один-entry не триггерит B2. Работает.

### 3. YT uppercase для S78/M78/TR56/M56, lowercase для Z56
- Z56 (WR3000H): `uci set podkop.yt=section`
- S78 (WR3000S) / M56 / TR56: `uci set podkop.YT=section`
Если перепутать — секция создаётся, но podkop её не видит как YT-профиль.

### 4. community_lists — порядок имеет значение
`telegram` и `meta` ВСЕГДА первыми. Стандартный набор (20 штук):
```
telegram meta geoblock block porn news anime discord twitter hdrezka tiktok
cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront
```
`russia_inside` — проверять явно, удалять если есть.

---

## Правило: Tailscale-соединение — священно

**Перед любой перезагрузкой роутера обязательно:**

1. Привести аргументы что роутер переживёт ребут:
   - `uci get tailscale.settings.fw_mode` → должно быть `none`
   - `/etc/init.d/tailscale enabled` → должно быть `DISABLED`
   - `grep tailscaled /etc/rc.local` → должна быть строка запуска
   - `crontab -l | grep watchdog` → watchdog должен быть
   - `uci get podkop.settings.exclude_ntp` → должно быть `1`

2. Только после того как все 5 пунктов ✅ — задать вопрос пользователю: "Можно ребутнуть?"

3. Никогда не ребутать молча. Никогда не ребутать если хотя бы один пункт ❌.

**Why:** Потеря Tailscale = потеря доступа к роутеру навсегда (до физического вмешательства).

---

## Workflow: Docker-бот на PL4 (82.38.66.75)

При изменении любого `.py` файла в `/opt/xui-bot/` — обязателен `docker compose build + up -d`.
Только `data/` и `bot.log` монтируются как volume. Остальное — внутри образа.

---

## Роутеры этой сессии

| Роутер | IP | Учётка | Что сделано |
|--------|-----|--------|-------------|
| S78-44 | 100.85.102.22 | ne78va | bSPB ключ, YT секция, community_lists, exclude_ntp |
