# Урок: настройка z56-84 — новый профиль bmsk-fin4-yt465 + podkop

**Дата:** 2026-05-07
**Роутер:** z56-84
**Профиль:** bmsk-fin4-yt465

---

## Суть задачи

Роутер z56-84 (клиент) нужно было перевести с прямого ApeCZ2 на связку bMSK→Fin4.
Особенность: YT должен идти через порт 465 (низкопортовый inbound на bMSK), а не через 8853 как в стандартном профиле bmsk-fin4.

---

## Что было сделано

### 1. Создан новый профиль в vless_key.py

Добавлен профиль `bmsk-fin4-yt465` — копия `bmsk-fin4`, но:
- **main** — без изменений: bMSK:5223 → Fin4 (inbound 1)
- **yt** — изменён: bMSK:465 (inbound 9) вместо bMSK:8853 (inbound 1)
  - pbk: `QfVJeoktRoCFJV6YdttWyGHMLnORut86toeStzTsUBk` (из inbound 9)
  - sid: `a3f7b2c1` (из inbound 9)
  - sni: `www.apple.com`, fp: `chrome`

### 2. Добавление клиентов в sqlite

**Проблема:** `vless_key.py` использует `repr(py)` для передачи Python-скрипта через SSH, что ломает экранирование кавычек.

**Решение:** Добавлять клиентов вручную через heredoc:
```bash
sshpass -p 'pass' ssh root@server "python3 << 'PYEOF'
import sqlite3, json, time
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
# ... код ...
PYEOF"
```

### 3. Устранение дубликата клиента

**Проблема:** xray не стартовал на bMSK с ошибкой:
```
User 19-ternovsky_YT already exists
```

**Причина:** в inbound 9 (порт 465) были дубликаты клиентов (2 записи с одинаковым email).

**Решение:** удалить дубликаты через sqlite:
```python
# Найти дубликаты по email
seen = {}
duplicates = []
for i, c in enumerate(clients):
    email = c.get('email', '')
    if email in seen:
        duplicates.append(i)
    else:
        seen[email] = i
# Удалить с конца (чтобы не сбить индексы)
for idx in sorted(duplicates, reverse=True):
    clients.pop(idx)
```

### 4. Настройка podkop

**Главное правило добавления community листов:**

> **Перед добавлением новых списков — ОБЯЗАТЕЛЬНО удалить старые через `uci del`!**
> Иначе `uci add_list` просто допишет новые к старым, и списки задвоятся.

Правильная последовательность:
```bash
# 1. Удалить старые
uci del podkop.main.community_lists 2>/dev/null || true

# 2. Добавить новые (telegram и meta — первыми, они самые важные)
for list in telegram meta geoblock block porn news anime discord twitter hdrezka tiktok cloudflare google_ai google_play hodca roblox hetzner ovh digitalocean cloudfront; do
  uci add_list podkop.main.community_lists="$list"
done

# 3. Сохранить
uci commit podkop
```

**Порядок списков имеет значение** — telegram и meta должны быть первыми, так как podkop обрабатывает их в приоритете.

### 5. Создание YT секции

```bash
uci set podkop.YT=section
uci set podkop.YT.connection_type="proxy"
uci set podkop.YT.proxy_string="vless://..."
uci set podkop.YT.proxy_config_type="url"
uci set podkop.YT.enable_udp_over_tcp="0"
uci add_list podkop.YT.community_lists="youtube"
uci commit podkop
```

### 6. Перезапуск podkop

```bash
/etc/init.d/podkop reload
```

**Важно:** `reload`, а не `restart` — чтобы не перезагружать sing-box без необходимости.

---

## Диагностика после настройки

### Как проверять что podkop работает:

1. **Проверить sing-box:**
   ```bash
   pgrep -a sing-box
   ```

2. **Проверить nftables:**
   ```bash
   nft list ruleset | grep -c "podkop"
   ```

3. **Проверить маршрутизацию (ключевой тест):**
   - Заблокированные сайты (telegram, rutracker, tiktok) должны резолвиться в `198.18.0.x`
   - Обычные сайты (google) — в реальный IP
   - YouTube — в `198.18.0.x` (через YT прокси)
   ```bash
   curl -s -o /dev/null -w "%{remote_ip}" https://youtube.com
   ```

4. **Проверить логи podkop:**
   ```bash
   logread -e podkop | tail -5
   ```

---

## Результаты z56-84

| Параметр | Значение |
|----------|----------|
| **WAN** | 109.173.66.13 (Ростелеком) |
| **Пинг bMSK** | 2.3 ms |
| **Пинг Fin4** | 27 ms |
| **Пинг Google** | 19.6 ms |
| **YouTube** | 🟢 0.17s через bMSK:465 |
| **Telegram** | 🟢 0.25s через bMSK→Fin4 |
| **TikTok** | 🟢 0.19s через bMSK→Fin4 |
| **Twitter** | 🟢 0.31s через bMSK→Fin4 |
| **Rutracker** | 🟢 0.24s через bMSK→Fin4 |
| **Discord** | 🟢 0.27s через bMSK→Fin4 |
| **Google** | 🟢 0.15s напрямую |

---

## Важные уроки

1. **`uci del` перед `uci add_list`** — иначе списки задвоятся
2. **`repr(py)` ломает кавычки** — используй heredoc `<< 'PYEOF'` для передачи Python через SSH
3. **Дубликаты клиентов в sqlite** — xray падает с `User already exists`. Лечится удалением дубликатов
4. **kill -9 xray** — после добавления клиента нужно убить процесс, systemd перезапустит сам
5. **198.18.0.0/15** — диапазон podkop для перенаправления трафика через прокси. Если сайт резолвится в этот диапазон — он идёт через прокси
