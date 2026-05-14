# Lesson: DE2 — создание VLESS-ключа без панели

## Дата
2026-05-13

## Проблема
DE2 (195.26.231.228) не имеет X-UI панели. xray запущен через `xray-direct.service` с конфигом `/usr/local/x-ui/bin/config.json`. Стандартный процесс (добавление через sqlite + kill -9) не работает, потому что нет БД x-ui.

## Решение

### 1. Добавить клиента через SSH + правка config.json

```bash
sshpass -p '24qbXK_EO-' ssh root@195.26.231.228

# Правим config.json
python3 << 'EOF'
import json
with open("/usr/local/x-ui/bin/config.json") as f:
    c = json.load(f)
for ib in c["inbounds"]:
    if ib.get("port") == <TARGET_PORT>:  # 4191, 4192, 2086
        if ib["settings"]["clients"] is None:
            ib["settings"]["clients"] = []
        ib["settings"]["clients"].append({"email": "<ROUTER_NAME>", "id": "<UUID>"})
with open("/usr/local/x-ui/bin/config.json", "w") as f:
    json.dump(c, f, indent=2)
EOF
```

### 2. Перезапустить xray-direct

```bash
# Убить старый процесс
kill $(pgrep -f "xray-linux-amd64.*config.json")
sleep 1
# Запустить через systemd
systemctl start xray-direct
# Проверить статус
systemctl is-active xray-direct  # должно быть "active"
```

### 3. Проверить через relay

```bash
echo "vless://UUID@159.194.198.172:5423?type=grpc&security=reality&mode=gun&serviceName=&pbk=iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo&sid=25fbd6cb&sni=www.apple.com&fp=chrome&spx=%2F#ROUTER_DE2" | python3 check_vless.py -
```

## Важные нюансы

1. **config.json может перезаписываться** — если x-ui (панель) запущен, он может перезаписать config.json из своей БД. На DE2 x-ui не запущен, только xray-direct.
2. **clients может быть null** — в config.json inbound может иметь `"clients": null`. Нужно проверять и заменять на `[]`.
3. **После kill старый процесс может не умереть сразу** — если systemctl start не сработал (port already in use), нужно явно kill PID.
4. **xray-direct.service может быть в статусе "activating"** — это нормально, если порт 11111 уже занят другим xray. Нужно убить все xray процессы.
5. **streamSettings может отсутствовать** — если x-ui сгенерировал config.json с багом, streamSettings для порта может быть null. Нужно восстановить вручную.

## ⚠️ КРИТИЧЕСКОЕ ПРАВИЛО: pbk для DE2

На DE2 **один privateKey на все порты** (4191, 4192, 2086).  
Поэтому **pbk одинаковый** для всех инбаундов: `iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo`

Не копировать pbk из X-UI панели — там может быть неверный pbk для конкретного порта.  
Бери pbk из RELAY_REFERENCE.json или MASTER_CREDENTIALS.md.

Если pbk не совпадает с серверным — **check_vless покажет READY** (потому что не проверяет pbk для неизвестных серверов), но **внутри подкопа ключ будет красным**.

## Доступные relay-схемы для DE2

| Relay | Цель | Тип | pbk | sid |
|-------|------|-----|-----|-----|
| bMSK:5090 | DE2:2086 | grpc+reality | iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo | 9fee82cd |
| bMSK:5423 | DE2:4191 | grpc+reality | iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo | 25fbd6cb |
| bMSK:5428 | DE2:4192 | grpc+reality | iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo | f98d9f37 |

## Связанные файлы

- `skills/create_vless_key/SKILL.md` — обновлён (добавлен шаг 3b для DE2)
- `ключи/RELAY_REFERENCE.json` — обновлён (исправлен pbk для msk_germany_4191)
- `SERVERS_RELAY_REFERENCE.md` — обновлён (исправлен pbk для DE2:2086)
