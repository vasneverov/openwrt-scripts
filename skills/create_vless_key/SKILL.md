# СКИЛЛ: Создание VLESS-ключа — create_vless_key

## Когда загружать

По командам:
- "создать ключ"
- "новый ключ VLESS"
- "сделай ключ для роутера"
- "ключ-клон"
- "нужен ключ на [страна]"

## ЖЕЛЕЗНЫЕ ПРАВИЛА

1. **`check_vless.py ● READY` НЕ значит что ключ рабочий!** — проверяет только TCP+TLS. UUID должен быть зарегистрирован в xray.
2. **Клиента добавлять через sqlite (SSH), НЕ через X-UI API.** API может не сохранить.
3. **После добавления — kill -9 xray.** Перезапуск через API не всегда работает.
4. **Перед созданием — спросить город.** СПб = bSPB relay, Москва = bMSK relay.
5. **Не создавать ключ если такой уже есть** — проверить в `ключи/KEY_CATALOG_ALL.md`.
6. **DE2 — без панели!** Клиентов добавлять через SSH + правка `/usr/local/x-ui/bin/config.json` + `kill` + `systemctl start xray-direct`.

## Источник данных

**Единый справочник:** `ключи/RELAY_REFERENCE.json`

Там все relay-схемы, прямые серверы, pbk/sid/inbound_id/SSH-пароли.

## Процесс

### Шаг 1: Определить параметры

| Вопрос | Ответ |
|--------|-------|
| Имя роутера | Например: TR56-13, Z56-94 |
| Город | spb (СПб) или msk (Москва) |
| Страна выхода | finland, poland, italy, czech, germany |
| Тип | main (по умолч.) или yt |

### Шаг 2: Запустить скрипт

```bash
python3 tools/create_vless_key.py <роутер> <город> <страна> [--type main|yt]
```

Скрипт делает всё сам:
1. Берёт схему из RELAY_REFERENCE.json
2. Генерирует UUID
3. Добавляет клиента через sqlite на целевом сервере (SSH)
4. Перезапускает xray (kill -9)
5. Собирает VLESS URL
6. Проверяет через check_vless.py
7. Сохраняет в `ключи/KEY_CATALOG_ALL.md`

### Шаг 3: Если SSH недоступен

Если SSH-пароль неизвестен — добавить клиента вручную через панель:
1. Открыть панель целевого сервера
2. Логин: `ad`, пароль: `56`
3. Найти inbound по ID
4. Добавить клиента с UUID и email
5. Перезапустить xray

### Шаг 3b: DE2 — особый случай (без панели)

DE2 не имеет X-UI панели. Клиентов добавлять ТОЛЬКО через SSH:

```bash
# 1. SSH на DE2
sshpass -p '24qbXK_EO-' ssh root@195.26.231.228

# 2. Править config.json (python3)
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

# 3. Перезапустить xray-direct
kill $(pgrep -f "xray-linux-amd64.*config.json")
sleep 1
systemctl start xray-direct
```

### ⚠️ ВАЖНО: pbk должен быть правильным

На некоторых серверах (особенно DE2) **pbk одинаковый для всех портов** — один privateKey на сервер.

**Перед проверкой ключа — убедись что pbk правильный:**
- DE2: pbk всегда `iR2cEt9NRvsSsuXR1f5cBgWZSkEzkmQjK5PX9YMt2Qo` (для 4191, 4192, 2086)
- FIN4: pbk всегда `HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI` (для 4191, 4192)
- PL5: pbk всегда `4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw` (для 4191, 4192)
- Italy: pbk всегда `OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI` (для 2083, 2086)

**Откуда брать pbk** — строго из `ключи/RELAY_REFERENCE.json` или таблицы ниже.

**Ошибка:** если pbk неверный → check_vless покажет `● READY` (TCP+TLS OK), но внутри подкопа ключ красный.

**Проверка pbk:**
```bash
# После check_vless — посмотри на строку "PubKey"
# Если pbk неизвестен → увидишь "pbk неизвестен — server checks пропущены!" (красное)
# Это значит pbk не совпадает с тем что на сервере — надо исправить
```

### Шаг 4: Проверить ключ

```bash
python3 check_vless.py <vless_url>
```

Ожидается: `● READY ✓✓✓`

### Шаг 5: Установить на роутер

```bash
uci set podkop.main.proxy_string="<vless_url>"
uci commit podkop
/etc/init.d/podkop restart
```

## Доступные схемы

### Relay (через российский сервер)

| Город | Страна | Relay | Цель | Label |
|-------|--------|-------|------|-------|
| spb | finland | bSPB:4191 -> Fin3:4191 | FI | Fin3 |
| spb | italy | bSPB:2090 -> Italy:2086 | IT | Italy |
| spb | czech | bSPB:8880 -> CZ3:8880 | CZ | ApeCZ3 |
| msk | finland | bMSK:5223 -> Fin4:4191 | FI | Fin4 |
| msk | finland | bMSK:5228 -> Fin4:4192 | FI | Fin4_2 |
| msk | poland | bMSK:5323 -> PL5:4191 | PL | PL5 |
| msk | poland | bMSK:5328 -> PL5:4192 | PL | PL5_2 |
| msk | germany | bMSK:5090 -> DE2:2086 | DE | DE2 |
| msk | germany | bMSK:5423 -> DE2:4191 | DE | DE2_4191 |
| msk | germany | bMSK:5428 -> DE2:4192 | DE | DE2_4192 |

### Direct (прямые серверы)

| Город | Тип | Сервер | Label |
|-------|-----|--------|-------|
| spb | yt | bSPB:8853 | bSPB_YT |
| msk | yt | bMSK:8853 | bMSK_YT |
| spb | main | bSPB:7443 | bSPB_direct_7443 |
| msk | main | bMSK:465 | bMSK_465 |

## Типичные ошибки

### Ошибка 1: Новый UUID без регистрации
```bash
# Неправильно
UUID=$(uuidgen)
echo "vless://$UUID@..." | check_vless.py -  # покажет READY
# НО UUID не в sqlite -> в LuCI красный
```

### Ошибка 2: Проверка только check_vless
```bash
# Неправильно - только TCP/TLS
check_vless.py показывает READY
# НО UUID не в xray config -> ключ красный
```

### Ошибка 3: DE2 - xray-direct не перезапущен
```bash
# Неправильно - клиент добавлен, но xray не перезагружен
# config.json обновлен, но старый процесс все еще работает
# Надо: kill + systemctl start xray-direct
```

### Правильно
```bash
# Правильно
1. Сгенерировать UUID
2. Добавить в sqlite/config.json на сервере
3. kill -9 xray (или systemctl restart)
4. Проверить grep UUID config.json
5. Только потом check_vless
6. Установить в подкоп
```

## Связанные файлы

- Справочник: `ключи/RELAY_REFERENCE.json`
- Скрипт: `tools/create_vless_key.py`
- Проверка: `check_vless.py`
- Каталог: `ключи/KEY_CATALOG_ALL.md`
- Железное правило: `IRON_RULES.md` - Правило 13
- Урок: `memory-lessons/lesson_check_vless_ready_not_working_2026-05-06.md`
- Урок: `memory-lessons/lesson_2026-05-13_de2_m56-24_relay_checkpoint.md`
