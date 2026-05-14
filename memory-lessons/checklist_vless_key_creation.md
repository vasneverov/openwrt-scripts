---
name: Чек-лист создания VLESS ключей (любая модель)
description: Железное правило создания рабочих ключей VLESS
type: reference
date: 2026-05-13
---

# Чек-лист создания VLESS ключей (любая модель)

## ⛔ Перед созданием ключа — ОБЯЗАТЕЛЬНО

### Шаг 1: Проверить сервер

```bash
# SSH на сервер
ssh root@SERVER_IP

# Проверить что xray запущен
pgrep xray
# Должен вернуть PID (число)
# Если пусто — ❌ xray НЕ работает, ключ не создавать!

# Проверить inbound
sqlite3 /etc/x-ui/x-ui.db "SELECT id,port,remark FROM inbounds WHERE id=INBOUND_ID"
# Запомнить: id, port

# Проверить pbk/sid в inbound
sqlite3 /etc/x-ui/x-ui.db "SELECT stream_settings FROM inbounds WHERE id=INBOUND_ID"
# Извлечь pbk и sid из JSON
```

### Шаг 2: Создать UUID

```bash
UUID=$(python3 -c "import uuid; print(str(uuid.uuid4()).upper())")
echo $UUID
```

### Шаг 3: Добавить в sqlite

```bash
python3 -c "
import sqlite3, json, time
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
row = conn.execute('SELECT settings FROM inbounds WHERE id=INBOUND_ID').fetchone()
data = json.loads(row[0])
data['clients'].append({
    'id': '$UUID',
    'email': 'ROUTER_NAME-main',
    'limitIp': 0,
    'totalGB': 1099511627776,
    'expiryTime': int((time.time() + 365*24*3600) * 1000),
    'enable': True,
    'tgId': '',
    'subId': '',
    'comment': ''
})
conn.execute('UPDATE inbounds SET settings=? WHERE id=INBOUND_ID', [json.dumps(data)])
conn.commit()
print(f'Clients: {len(data[\"clients\"])}')
"
```

### Шаг 4: Перезапустить xray

```bash
kill -9 $(pgrep xray)
sleep 3
pgrep xray && echo "✅ xray running" || echo "❌ xray NOT running"
```

### Шаг 5: Проверить UUID в config

```bash
grep -c '$UUID' /usr/local/x-ui/bin/config.json
# Должно быть > 0
```

### Шаг 6: check_vless.py

```bash
echo 'vless://UUID@IP:PORT?type=grpc&security=reality...' | python3 check_vless.py -
# Ожидаем: ● READY ✓✓✓
```

### Шаг 7: Вставить в роутер

ТОЛЬКО после ● READY ✓✓✓

---

## Проверка портов

| Сервер | Inbound ID | Port | Статус (2026-05-13) |
|--------|------------|------|---------------------|
| bSPB | 1 | 6443 | ❌ xray сломан |
| bSPB | 6 | 2090 | ❌ xray сломан |
| bMSK | 21 | 587 | ✅ Работает (Fin4) |
| bMSK | 22 | 8880 | ✅ Работает (CZ3) |
| bMSK | 1 | 8853 | ✅ Работает (YT) |

---

## Критичные ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| Ключ READY но не работает | xray не запущен | Проверить `pgrep xray` |
| Ключ READY но не работает | Неправильный порт | Проверить `SELECT port FROM inbounds` |
| Ключ READY но не работает | Неправильный pbk/sid | Проверить `SELECT stream_settings FROM inbounds` |
| Ключ красный в LuCI | Нет UUID в xray config | Проверить `grep UUID /usr/local/x-ui/bin/config.json` |

---

## Ссылки

- [Полный урок M56-24](../../../../../CLAUDECODE/memory-lessons/lesson_2026-05-13_key_creation_failures.md)
- [check_vless.py](../../../../../CLAUDECODE/check_vless.py)
