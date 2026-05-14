# lesson: fix_json_parsers_process_sh — 2026-05-12

## Проблема
`process.sh` на сервере 144.31.244.181 использовал `grep -o '{.*}'` для извлечения JSON из вывода DeepSeek. `grep` работает построчно и не находит многострочный JSON. В результате capture/execute фазы падали с `{"error": "failed to parse..."}`.

## Решение
1. Заменил `grep -o '{.*}' | python3 -c "..."` на вызов внешнего скрипта `parse_json.py`
2. `parse_json.py` использует depth-based парсинг: считает `{`/`}` и находит первый валидный JSON-объект, даже если он многострочный
3. Использует `os._exit(0)` для немедленного выхода после успешного парсинга

## Файлы
- `/home/sbrain/sbrain/scripts/process.sh` — изменён (строки 145, 168)
- `/home/sbrain/sbrain/scripts/parse_json.py` — создан

## Команда проверки
```bash
echo 'text {"a": 1, "b": {"c": 2}} text' | python3 /home/sbrain/sbrain/scripts/parse_json.py
```
