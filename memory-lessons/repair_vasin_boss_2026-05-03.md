---
name: Vasin_BOSS (100.122.66.80) — восстановление UUID main после PL5 миграции
description: UUID пропал из proxy_string, создан новый и добавлен на PL5
router: Vasin_BOSS
tailscale_ip: 100.122.66.80
account: vas.neverov
date: 2026-05-03
server: PL5
---

# Ремонт Vasin_BOSS — восстановление main профиля

## Симптомы
- Main профиль красный в LuCI podkop
- telegram: 000 (не работал)
- youtube: 200 (YT профиль работал)
- После обновления pbk → telegram всё ещё 000

## Диагностика

### Проверка proxy_string
```bash
uci get podkop.main.proxy_string
# Результат: vless://@159.194.198.172:5323?...
# UUID отсутствовал (пустое значение между vless:// и @)
```

### Проверка на PL5
UUID не был найден в /usr/local/x-ui/bin/config.json — клиент потерян при миграции.

## Исправление

### Шаг 1: Создание нового UUID
```
5e7d5930-3c59-4c33-8195-a212f1c2e181
```

### Шаг 2: Добавление на PL5 через sqlite3
```python
import sqlite3, json, time
DB = '/etc/x-ui/x-ui.db'
conn = sqlite3.connect(DB)
row = conn.execute('SELECT settings FROM inbounds WHERE id=1').fetchone()
data = json.loads(row[0])
data['clients'].append({
    'id': '5e7d5930-3c59-4c33-8195-a212f1c2e181',
    'email': 'Vasin_BOSS',
    'limitIp': 0,
    'totalGB': 1099511627776,
    'expiryTime': int((time.time() + 365*24*3600) * 1000),
    'enable': True,
    'tgId': '', 'subId': '', 'comment': ''
})
conn.execute('UPDATE inbounds SET settings=? WHERE id=1', [json.dumps(data)])
conn.commit()
```

### Шаг 3: Перезапуск xray на PL5
```bash
kill -9 $(pgrep xray)
# Проверка: grep -c '5e7d5930-3c59-4c33-8195-a212f1c2e181' /usr/local/x-ui/bin/config.json
# Результат: 1 ✓
```

### Шаг 4: Проверка ключа
```bash
echo 'vless://5e7d5930-3c59-4c33-8195-a212f1c2e181@159.194.198.172:5323?type=grpc&security=reality&mode=gun&serviceName=&pbk=RQN8c9kjYV_jlTCgeHIIidKgfQbEeg12Hd5_sfiBURs&sid=b5023350&sni=www.apple.com&fp=chrome&spx=%2F#Vasin_BOSS_PL5' | python3 ~/CLAUDECODE/check_vless.py -
# Результат: ● READY ✓✓
```

### Шаг 5: Обновление на роутере
```bash
uci set podkop.main.proxy_string='vless://5e7d5930-3c59-4c33-8195-a212f1c2e181@159.194.198.172:5323?type=grpc&security=reality&mode=gun&serviceName=&pbk=RQN8c9kjYV_jlTCgeHIIidKgfQbEeg12Hd5_sfiBURs&sid=b5023350&sni=www.apple.com&fp=chrome&spx=%2F#Vasin_BOSS-main-relay-PL5'
uci commit podkop
/etc/init.d/podkop restart
```

## Результаты тестов

| Сервис | Код | Статус |
|--------|-----|--------|
| telegram | 200 | ✅ |
| youtube | 200 | ✅ |
| google | 200 | ✅ |

## Уроки

1. **Пустой UUID в proxy_string** — если после `vless://` сразу `@`, UUID пропал
2. **После pbk update всё ещё 000** → проверять UUID на сервере
3. **Новый UUID через sqlite3** — надёжнее чем искать старый
4. **Суффикс `-relay`** добавлен к имени ключа для ясности топологии

## Файлы ключей

Создать файл: `~/CLAUDECODE/ключи/vless_vasin_boss_pl5_main.md`

```markdown
# VLESS Key — Vasin_BOSS main → PL5 (bMSK relay)

- Router: Vasin_BOSS (100.122.66.80)
- Account: vas.neverov
- Server: PL5 via bMSK relay
- Profile: main
- Created: 2026-05-03

## Connection Details

- UUID: `5e7d5930-3c59-4c33-8195-a212f1c2e181`
- Relay: bMSK 159.194.198.172:5323 → PL5:4191
- pbk: `RQN8c9kjYV_jlTCgeHIIidKgfQbEeg12Hd5_sfiBURs`
- sid: `b5023350`
- sni: `www.apple.com`

## VLESS URL

```
vless://5e7d5930-3c59-4c33-8195-a212f1c2e181@159.194.198.172:5323?type=grpc&security=reality&mode=gun&serviceName=&pbk=RQN8c9kjYV_jlTCgeHIIidKgfQbEeg12Hd5_sfiBURs&sid=b5023350&sni=www.apple.com&fp=chrome&spx=%2F#Vasin_BOSS-main-relay-PL5
```
```
