# Урок: S78-44 — правильный pbk для PL5

**Дата:** 2026-05-04  
**Роутер:** S78-44 (100.85.102.22, Cudy WR3000S v1, ne78va)  
**Проблема:** Main профиль красный в LuCI, telegram 000

---

## Что было сделано

1. **Применён спасательный скрипт** — fw_mode=none, init.d disabled, watchdog'и
2. **Созданы новые ключи** — московская схема (PL5 + bMSK)
3. **Проблема:** Reality verification failed

## Корневая причина

**Неправильный pbk для PL5.**

Было использовано (НЕПРАВИЛЬНО):
```
pbk=4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw
```

Правильный pbk для PL5 (порт 4191):
```
pbk=RQN8c9kjYV_jlTCgeHIIidKgfQbEeg12Hd5_sfiBURs
sid=b5023350
```

## Результат

| Профиль | UUID | Статус |
|---------|------|--------|
| main | b79c9d2b-c3dd-4a8d-9f5d-22c172887809 | ✅ ЗЕЛЁНЫЙ |
| YT | 93714931-aae8-4dfc-8579-23ec1ebbc149 | ✅ ЗЕЛЁНЫЙ |

Тесты: telegram 200, youtube 200, google 200 ✅

## Железное правило

**Всегда проверять pbk в свежих записях memory.** Разные роутеры могут иметь разные pbk в зависимости от даты создания.

---
**pbk PL5:** `RQN8c9kjYV_jlTCgeHIIidKgfQbEeg12Hd5_sfiBURs`  
**sid PL5:** `b5023350`
