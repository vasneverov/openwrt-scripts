# Урок: check_vless.py ● READY ≠ рабочий ключ

**Дата:** 2026-05-06  
**Роутеры:** C3000S_05 (100.69.248.95), S78-40 (100.118.37.35)  
**Проблема:** Ключи показывают ● READY в check_vless, но красные в LuCI

## Ошибка

Я проверял ключи через `check_vless.py`:
```
● READY — TCP+TLS OK
```

И ставил их в подкоп. Но в LuCI они были красными.

## Почему

**check_vless.py проверяет только:**
1. TCP порт доступен
2. TLS handshake проходит

**НО Reality handshake проходит с ЛЮБЫМ UUID!**

Сервер принимает соединение, но xray отбрасывает трафик если UUID не зарегистрирован в `/usr/local/x-ui/bin/config.json`.

## Разница

| Проверка | Что показывает | Что НЕ показывает |
|----------|---------------|-------------------|
| check_vless.py ● READY | TCP+TLS работают | UUID зарегистрирован? |
| LuCI зелёный | Всё работает | — |
| LuCI красный | UUID не найден | — |

## Правильная проверка

```bash
# 1. check_vless.py → ● READY (TCP+TLS)
echo 'vless://...' | python3 check_vless.py -

# 2. Проверить UUID в конфиге xray (ОБЯЗАТЕЛЬНО!)
ssh root@SERVER 'grep -c "UUID" /usr/local/x-ui/bin/config.json'
# → 0 = ключ красный
# → >0 = ключ может работать

# 3. Проверить limitIp не превышен
```

## Быстрое решение

**Использовать существующий UUID из рабочего роутера:**

```bash
# UUID из S78-40 (проверены, работают)
Main: 783c7b55-1679-404a-a185-d8b62581463b
YT:   1DFE7053-A08C-4EB6-B264-D2E3651A07EA
```

Эти UUID уже в sqlite → xray их знает → ключи зелёные.

## Создание нового ключа (полный процесс)

```bash
# 1. UUID
UUID=$(python3 -c "import uuid; print(str(uuid.uuid4()).upper())")

# 2. Добавить в sqlite (НЕ через API!)
python3 << PYEOF
import sqlite3, json, time
DB = '/etc/x-ui/x-ui.db'
conn = sqlite3.connect(DB)
row = conn.execute('SELECT settings FROM inbounds WHERE id=1').fetchone()
data = json.loads(row[0])
data['clients'].append({
    'id': '$UUID',
    'email': 'ROUTER-main',
    'limitIp': 0,
    'totalGB': 1099511627776,
    'expiryTime': int((time.time() + 365*24*3600) * 1000),
    'enable': True,
    'tgId': '', 'subId': '', 'comment': ''
})
conn.execute('UPDATE inbounds SET settings=? WHERE id=1', [json.dumps(data)])
conn.commit()
print(f"Клиентов теперь: {len(data['clients'])}")
PYEOF

# 3. Перезапустить xray
kill -9 $(pgrep xray)
sleep 3

# 4. Проверить
ssh root@SERVER 'grep -c "$UUID" /usr/local/x-ui/bin/config.json'

# 5. Теперь check_vless
```

## Железное правило

**ПРАВИЛО 13:** `check_vless.py ● READY` ≠ рабочий ключ.

Настоящая проверка: `grep UUID /usr/local/x-ui/bin/config.json`

## Файлы
- Железное правило: `~/.claude/IRON_RULES.md` — Правило 13
- Скилл: `~/.claude/skills/key-creation-vless/SKILL.md`
