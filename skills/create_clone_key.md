# Скилл: Создать ключ-клон для роутера

> Когда пользователь говорит: *"сделай мне точно такой же ключ для этого роутера"* — это значит создать **копию текущего профиля Main, но с новым UUID**.

---

## Алгоритм

### Шаг 1. Получить текущий proxy_string с роутера

```bash
sshpass -p '56756789' ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no \
  -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@<TAILSCALE_IP> "
uci get podkop.main.proxy_string
"
```

Из строки извлечь:
- **relay_ip** (хост после @)
- **relay_port** (порт после двоеточия)
- **pbk** (public key для REALITY)
- **sid** (short ID)
- **sni** (server name)
- **fp** (fingerprint)

### Шаг 2. Определить, на каком X-UI сервере создавать клиента

Посмотреть в `MASTER_CREDENTIALS.md`:
- Если pbk известен — найти сервер по pbk в таблице PBK/SID
- Если pbk НЕ известен — найти сервер по IP в списке X-UI серверов

**ВАЖНО: НЕ использовать API напрямую через curl.** Только через `create_vless_key.py` или `add_fin3_client.sh`.

### Шаг 3. Посмотреть список инбаундов на сервере

Зайти на панель через браузер или использовать `create_vless_key.py` с `--dry-run`.

URL панели: `https://<SERVER_IP>:5050/5050/`
Логин: `ad` / пароль: `56`

Найти inbound с нужным портом. Запомнить **inbound_id**.

### Шаг 4. Создать нового клиента

Использовать `create_vless_key.py` с ручными параметрами:

```bash
python3 /Users/vas/CLAUDECODE/tools/create_vless_key.py \
  --router <ROUTER_NAME> \
  --panel-ip <PANEL_HOST> \
  --panel-port 5050 \
  --inbound-id <INBOUND_ID> \
  --relay-ip <RELAY_IP> \
  --relay-port <RELAY_PORT> \
  --pbk "<PBK>" \
  --sid "<SID>"
```

Скрипт:
1. Логинится на панель (ad/56)
2. Проверяет, нет ли уже клиента с таким email
3. Генерирует новый UUID
4. Добавляет клиента с лимитами: 365 дней / 1 TB
5. Выводит готовый VLESS ключ

### Шаг 5. Проверить новый ключ

```bash
python3 /Users/vas/CLAUDECODE/check_vless.py "vless://<NEW_UUID>@..."
```

Должен быть **TCP OK** + **TLS OK** → **READY**.

### Шаг 6. Заменить ключ на роутере (без перезагрузки Podkop)

```bash
sshpass -p '56756789' ssh ... root@<TAILSCALE_IP> "
uci set podkop.main.proxy_string='vless://<NEW_UUID>@...'
uci commit podkop
"
```

**НЕ перезагружать podkop.** Только `uci set` + `uci commit`. Изменения применятся при следующем перезапуске podkop (watchdog или перезагрузка роутера).

---

## Почему НЕЛЬЗЯ использовать API напрямую через curl

1. **X-UI API нестабилен** — разные версии панелей имеют разные эндпоинты
2. **Ошибка аутентификации** — куки могут не сохраниться, сессия истекает
3. **Нет проверок** — можно случайно создать дубликат или сломать конфиг
4. **Нет лимитов** — можно создать клиента без expiryTime/totalGB

Использовать только `create_vless_key.py` — он:
- Правильно логинится
- Проверяет существующих клиентов
- Ставит корректные лимиты (365 дней / 1 TB)
- Генерирует правильный VLESS URL

---

## Что такое kill -9

`kill -9 <PID>` — принудительное завершение процесса. Используется, когда нужно перезапустить xray/sing-box без перезагрузки всего сервиса.

**Когда применять:**
- После добавления нового клиента на панели, если он не появляется в активном конфиге
- `kill -9 $(pgrep xray)` — xray перезапустится автоматически (через systemd/supervisor)
- `kill -9 $(pgrep sing-box)` — sing-box перезапустится через watchdog

**НЕ применять на роутере** — там sing-box управляется podkop watchdog.

---

## Где брать пароли

| Что | Где |
|-----|-----|
| SSH на роутеры | `MASTER_CREDENTIALS.md` → `56756789` |
| X-UI панели | `MASTER_CREDENTIALS.md` → `ad` / `56` |
| SSH на серверы | `MASTER_CREDENTIALS.md` → по IP |
| Tailscale токены | `TAILSCALE_TOKENS.md` |
| Relay топология | `SERVERS_RELAY_REFERENCE.md` |

---

## Железные правила (дополнение к IRON_RULES.md)

1. **Ключ-клон = тот же сервер + тот же порт + тот же pbk + тот же sid + новый UUID**
2. **НЕ создавать новый профиль** — заменять UUID в существующем
3. **НЕ перезагружать podkop** после замены ключа — только uci commit
4. **НЕ использовать curl к API** — только create_vless_key.py
5. **Всегда проверять ключ** через check_vless.py перед установкой
6. **Если pbk неизвестен** — искать сервер по IP в MASTER_CREDENTIALS.md
