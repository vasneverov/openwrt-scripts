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

## Источник данных

**Единый справочник:** `ключи/RELAY_REFERENCE.json`

Там все relay-схемы, прямые серверы, pbk/sid/inbound_id/SSH-пароли.

## Процесс

### Шаг 1: Определить параметры

| Вопрос | Ответ |
|--------|-------|
| Имя роутера | Например: TR56-13, Z56-94 |
| Город | spb (СПб) или msk (Москва) |
| Страна выхода | finland, poland, italy, czech |
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
| spb | finland | bSPB:4191 → Fin3:4191 | 🇫🇮 | Fin3 |
| spb | italy | bSPB:2090 → Italy:2086 | 🇮🇹 | Italy |
| spb | czech | bSPB:8880 → CZ3:8880 | 🇨🇿 | ApeCZ3 |
| msk | finland | bMSK:5223 → Fin4:4191 | 🇫🇮 | Fin4 |
| msk | finland | bMSK:5228 → Fin4:4192 | 🇫🇮 | Fin4_2 |
| msk | poland | bMSK:5323 → PL5:4191 | 🇵🇱 | PL5 |
| msk | poland | bMSK:5328 → PL5:4192 | 🇵🇱 | PL5_2 |

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
# ❌ Неправильно
UUID=$(uuidgen)
echo "vless://$UUID@..." | check_vless.py -  # покажет ● READY
# НО UUID не в sqlite → в LuCI красный
```

### Ошибка 2: Проверка только check_vless
```bash
# ❌ Неправильно — только TCP/TLS
check_vless.py показывает ● READY
# НО UUID не в xray config → ключ красный
```

### Правильно
```bash
# ✅ Правильно
1. Сгенерировать UUID
2. Добавить в sqlite на сервере
3. kill -9 xray
4. Проверить grep UUID /usr/local/x-ui/bin/config.json
5. Только потом check_vless
6. Установить в подкоп
```

## Связанные файлы

- Справочник: `ключи/RELAY_REFERENCE.json`
- Скрипт: `tools/create_vless_key.py`
- Проверка: `check_vless.py`
- Каталог: `ключи/KEY_CATALOG_ALL.md`
- Железное правило: `IRON_RULES.md` — Правило 13
- Урок: `memory-lessons/lesson_check_vless_ready_not_working_2026-05-06.md`
