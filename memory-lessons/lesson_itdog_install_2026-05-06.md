# Урок: Установка podkop через itdog скрипт (06.05.2026)

**Роутер:** 17-usievicha10-6 (Xiaomi AX3000T, OpenWrt 24.10.1, opkg)
**Задача:** Удалили старый podkop v0.4.4, установили v0.7.14 + sing-box 1.12.22 (полный)

---

## Правильный способ (работает)

```bash
# Шаг 1: скачать скрипт
wget -qO /tmp/install.sh https://raw.githubusercontent.com/itdoginfo/podkop/refs/heads/main/install.sh

# Шаг 2: запустить с heredoc (y = русский язык)
sh /tmp/install.sh << INPUT
y
INPUT
```

Скрипт сам определяет менеджер пакетов (opkg/apk), устанавливает podkop + luci + sing-box.

---

## Что НЕ работает

| Метод | Проблема |
|---|---|
| `yes y \| sh <(wget -O - URL)` | Зависает — yes пишет y бесконечно, блокирует скрипт |
| `printf 'y\n' \| sh <(...)` | Тоже зависает при process substitution |
| `cat all.ipk \| opkg install --nodeps` | Ошибка "incompatible with architectures configured" для all.ipk |
| `opkg install --nodeps --force-architecture` | Не помогает для all.ipk |

---

## КРИТИЧНО: russia_inside после itdog

**itdog скрипт автоматически добавляет `russia_inside` в community_lists.**

Это нужно удалять СРАЗУ после установки, до настройки ключей:

```bash
uci del_list podkop.settings.community_lists='russia_inside' 2>/dev/null
uci commit podkop
# Проверить что telegram и meta первые:
uci get podkop.settings.community_lists
```

---

## Для 25.12 (apk роутеры)

Тот же скрипт, то же скачивание. Скрипт сам использует `apk add` вместо `opkg install`.

---

## Источник: ROUTER_REPAIR_GUIDE.md

Зафиксировано в секции "Особые случаи" → "Установка podkop через itdog скрипт" и Топ-10 ошибок п.11.
