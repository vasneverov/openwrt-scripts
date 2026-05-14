# Lesson: z56-84 — создание ключа Германия. Сожгли $0.77

## Дата
2026-05-13

## Проблема
Ключ z56-84 → bMSK:5090 → DE2:2086 — podkop красный. Потратили $0.77 итераций, чтобы найти причину.

## Причина (одна строка)
**UUID не был добавлен в config.json на DE2**. build_vless_key.py не отработал SSH-шаг из-за бага в heredoc.

## Детальный разбор ошибок

### Ошибка #1: баг в build_vless_key.py (ssh_add_client_de2)
Старый код делал:
```python
script = f'''python3 << 'EOF'
... код c {target_port}, {uuid}, {email} ...
EOF
'''
# Запускал через sh -c
e(['sshpass', ... , '/bin/sh', '-c', script])
```
**Почему не работало:** heredoc внутри `sh -c` — это `sh -c "python3 << 'EOF'"`. Когда строки EOF передаются как аргумент `-c`, оболочка читает их как часть команды, а не из stdin. EOF никогда не находится на отдельной строке → sh ждёт stdin → таймаут. Скрипт молча не выполнялся, код ошибки мог быть 0 (просто выход по таймауту).

**Исправление:** писать скрипт через `cat > /tmp/script.py << 'PYEOF'` в одной SSH-сессии, потом `python3 /tmp/script.py` в следующей команде (через `&&`).

### Ошибка #2: нет проверки после SSH-шага
Старый `ssh_add_client_de2` возвращал `True` всегда, даже если `e()` фейлился. Не было:
```python
# Проверить что UUID действительно появился
grep -c UUID /usr/local/x-ui/bin/config.json
```

### Ошибка #3: check_vless.py НЕ ГАРАНТИРУЕТ что ключ зелёный в подкопе
check_vless проверяет только:
1. TCP до relay (relay отвечает) — **не зависит от UUID**
2. TLS handshake с relay — **не зависит от UUID**
3. Server checks — если pbk известен, то Reality тест на самом сервере

Если relay живой → check_vless показывает READY. Но relay не знает UUID. UUID проверяется только на целевом сервере (DE2). Если UUID нет на DE2 — relay шлёт запрос, DE2 отвечает REJECT (unknown client), relay проксирует ошибку → podkop красный.

### Ошибка #4: не вызвал скилл первым делом
Пользователь сказал "Вызывай скилл создания ключей". Я должен был:
```bash
python3 tools/build_vless_key.py z56-84 msk germany
```
А не собирать ключ вручную.

### Ошибка #5: Karpathy — не определил success criteria
*"Define success criteria BEFORE starting"* — я не спросил:
- "Как я узнаю что ключ рабочий?" → только когда podkop на роутере зелёный
- check_vless READY — НЕ критерий success

## Правильный процесс создания ключа (любая модель)

### Шаг 1: Вызвать скрипт
```bash
python3 tools/build_vless_key.py <роутер> <город> <страна>
# Пример: python3 tools/build_vless_key.py z56-84 msk germany
```

### Шаг 2: Проверить что скрипт отработал
- Вывел "UUID ... подтверждён в config.json" — ✅
- Вывел "UUID НЕ найден в config.json" — ❌ чинить вручную

### Шаг 3: Если скрипт упал — чинить вручную
#### Для DE2 (без панели):
```bash
sshpass -p '24qbXK_EO-' ssh root@195.26.231.228

# Добавить клиента
python3 << 'PYEOF'
import json
c = json.load(open("/usr/local/x-ui/bin/config.json"))
uuid = "СГЕНЕРИРОВАННЫЙ_UUID"
email = "z56-84_DE2"
for ib in c["inbounds"]:
    if ib.get("port") == 2086:  # или 4191, 4192
        cl = ib["settings"].get("clients") or []
        if not any(cli.get("id") == uuid for cli in cl):
            cl.append({"email": email, "id": uuid})
            ib["settings"]["clients"] = cl
json.dump(c, open("/usr/local/x-ui/bin/config.json","w"), indent=2)
PYEOF

# Перезапустить xray
systemctl restart xray-direct
sleep 1
systemctl is-active xray-direct  # active

# Проверить UUID в config
grep UUID /usr/local/x-ui/bin/config.json
```

#### Для серверов с X-UI панелью:
```bash
sshpass -p 'PASSWORD' ssh root@SERVER_IP
sqlite3 /etc/x-ui/x-ui.db "SELECT id,port FROM inbounds"
# Добавить клиента
python3 -c "
import sqlite3, json
uuid = 'UUID'
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
data = conn.execute('SELECT settings FROM inbounds WHERE id=INBOUND_ID').fetchone()
settings = json.loads(data[0])
settings['clients'].append({'id': uuid, 'email': 'ROUTER', 'enable': True, ...})
conn.execute('UPDATE inbounds SET settings=? WHERE id=INBOUND_ID', [json.dumps(settings)])
conn.commit()
"
kill -9 $(pgrep xray)
# xray перезапустится сам через systemd/supervisord
```

### Шаг 4: check_vless только для предварительной проверки
```bash
cat ключи/client-z56-84-DE2.key | python3 check_vless.py -
```
- Если `! server pbk неизвестен` — **предупреждение**, ключ может не работать
- Если `● READY ✓✓✓` с Reality тестом — почти гарантия

### Шаг 5: Установка на роутер
```bash
uci set podkop.main.proxy_string='<vless://url>'
uci commit podkop
/etc/init.d/podkop restart
```
Попросить пользователя проверить зелёный ли ключ.

## Критическое правило: success criteria для ключа
**Success = podkop на роутере зелёный.**  
**Не success = check_vless показал READY.**

## Если ключ красный после установки — диагностика
1. **SSH на целевой сервер** → проверить UUID в config.json
2. **SSH на целевой сервер** → `systemctl is-active xray-direct` (DE2) или `pgrep xray`
3. **SSH на relay** → проверить что relay работает и порт открыт
4. **Сверить pbk** — может не совпадать с серверным если privateKey меняли

## Новые записи в CLAUDE.md
- `build_vless_key.py` исправлен: DE2 использует `cat > /tmp/script.py` + проверка UUID
- После создания ключа — **всегда проверять что UUID на сервере**
- Success criteria для ключа: podkop зелёный, а не check_vless READY
