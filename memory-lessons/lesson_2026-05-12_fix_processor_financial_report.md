# Fix: processor.py — финансовый отчёт вместо упрощённого

## Проблема
Кнопка "⚙️ Обработать" → `cmd_process()` → `DeepSeekProcessor.process_daily()` (Python-класс).
Класс генерировал упрощённый отчёт (classify entries, process entries, generate report) без контекста финансов, продаж, балансов.

Правильный отчёт (который был раньше) содержит:
- Расходы по картам
- Продажи роутеров (март/апрель/май)
- Балансы карт (Сбер, Т-банк, Яндекс, WB, нал, нал $)
- Траты Антона
- Дебиторка
- Вес (динамика)
- Итог дня (доходы/расходы)

## Корень
`processor.py` использовал `json.loads()` напрямую, без очистки от markdown-обёртки (` ```json ... ``` `). DeepSeek иногда возвращает JSON с обёрткой → `json.loads()` падал → execute возвращал пустой результат → отчёт был пустой.

## Что сделано
1. Добавлена функция `_clean_json()` — удаляет ` ```json ` и ` ``` ` обёртки
2. Добавлена функция `_parse_json()` — пробует json.loads, затем depth-based парсинг
3. Добавлен метод `_get_vault_context()` — читает MEMORY.md, goals/, последние 7 daily/ для контекста
4. Переписан `_phase_reflect()` — промпт генерирует финансовый отчёт в нужном формате
5. `process_daily()` теперь передаёт vault_context в Phase 3

## Файлы
- `/home/sbrain/sbrain/src/d_brain/services/processor.py` — новый (342 строки)
- `/home/sbrain/sbrain/src/d_brain/services/processor.py.bak` — бэкап старого

## Команды
```bash
systemctl restart d-brain-bot
```
