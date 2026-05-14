# d-brain Bot Architecture — полная карта

## Структура vault

### Ключевые файлы
- `MEMORY.md` — долгосрочная память: финансы, инвентарь роутеров, правила
- `routers.md` — заметки по роутерам
- `business/inventory.md` — отдельный файл инвентаря
- `business/crm/*.md` — CRM каждого клиента
- `daily/YYYY-MM-DD.md` — ежедневные записи

### Claude Skills (системные промпты для DeepSeek)
- `.claude/skills/dbrain-processor/SKILL.md` — **главный** промпт для DeepSeek
- `references/rules.md` — обязательные правила обработки
- `references/classification.md` — правила классификации записей
- `references/report-template.md` — шаблон отчёта
- `references/business-context.md` — контекст бизнеса
- `references/goals.md` — цели
- `references/contacts.md` — контакты
- `references/links.md` — построение wiki-ссылок
- `phases/capture.md` — инструкция для фазы CAPTURE
- `phases/execute.md` — инструкция для фазы EXECUTE
- `phases/reflect.md` — инструкция для фазы REFLECT

## Как работал старый pipeline (process.sh → DeepSeek)

1. **ORIENT**: проверка файлов, таймзона
2. **CAPTURE**: DeepSeek классифицирует записи дня
3. **EXECUTE**: DeepSeek получает полный контекст (SKILL + MEMORY + references) → 
   - Обновляет MEMORY.md (инвентарь роутеров, финансы)
   - Создаёт мысли (thoughts/)
   - Логирует в daily/
4. **REFLECT**: DeepSeek генерирует HTML-отчёт по шаблону из SKILL.md

## Что сломалось сейчас

Я заменил DeepSeek в REFLECT на чистый Python (finance_report.py), но:
1. Python не понимает контекст роутеров, клиентов, бизнеса
2. DeepSeek в EXECUTE не получает достаточно контекста (нет инвентаря роутеров)
3. SKILL.md не используется как системный промпт

## Что нужно восстановить завтра

1. **EXECUTE**: DeepSeek должен получать полный контекст (SKILL + MEMORY + inventory)
2. **REFLECT**: DeepSeek генерирует отчёт по ШАБЛОНУ из SKILL.md
3. **Убрать из шаблона**: focus/tasks/goals — если пользователь их не хочет
4. **ОСТАВИТЬ**: finance_report.py как fallback/проверку

## Текущие изменения (13.05 01:20)
- finance_tracker.py — детектирует транзакции ✅
- finance_report.py — генерирует финансовый отчёт ✅
- processor.py — 3 фазы с DeepSeek + finance_tracker ✅
- process.py handler — cubes + русский язык ✅
- Таймзона: Europe/Moscow ✅
