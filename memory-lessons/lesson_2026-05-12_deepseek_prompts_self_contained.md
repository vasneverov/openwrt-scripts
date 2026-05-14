# lesson: deepseek_prompts_self_contained — 2026-05-12

## Проблема
DeepSeek не следует инструкциям "прочитай файл X и сделай как там написано". Вместо классификации записей он возвращает мета-информацию о прочитанных файлах. Обработка проходит за 15 секунд вместо 3-4 минут.

## Причина
DeepSeek плохо понимает косвенные инструкции через внешние .md файлы. Промпты вида "Read .claude/skills/dbrain-processor/phases/capture.md and execute Phase 1" приводят к тому что DeepSeek просто перечисляет что он прочитал, а не выполняет задачу.

## Решение
Все инструкции встроены прямо в промпт. Каждый промпт содержит:
1. Конкретную задачу (classify entries / create tasks / generate report)
2. Точную структуру JSON на выходе
3. Запрет на пояснения и markdown

## Изменённые файлы
- `/home/sbrain/sbrain/scripts/process.sh` — промпты для Phase 1, 2, 3

## Структура промптов

### Phase 1: CAPTURE
```
"Today is $TODAY. Read $DAILY_REL.
For each entry (## HH:MM [type] block), classify as: task, idea, reflection, learning, project, crm_update, or skip.
Return ONLY valid JSON with this exact structure:
{
  "date": "$TODAY",
  "entries": [
    {
      "time": "HH:MM",
      "type": "voice|text|photo",
      "content": "entry text",
      "classification": "task|idea|...",
      "task_content": "if task, what to do",
      "task_priority": 1-4,
      "entities": []
    }
  ],
  "stats": {"total_entries": 0, "tasks": 0, "thoughts": 0, "skipped": 0}
}
NO explanation. NO markdown. ONLY JSON."
```

### Phase 2: EXECUTE
```
"Today is $TODAY. Read .session/capture.json.
For each entry with classification 'task': create a task entry.
For each entry with classification 'idea|reflection|learning|project': create a thought entry.
Return ONLY valid JSON with this exact structure:
{
  "tasks_created": [{"content": "task text", "priority": 2}],
  "thoughts_saved": [{"title": "thought title", "category": "ideas|..."}],
  "observations": []
}
NO explanation. NO markdown. ONLY JSON."
```

### Phase 3: REFLECT
```
"Today is $TODAY. Read .session/capture.json and .session/execute.json.
Generate a daily report in HTML format for Telegram.
Include: date, summary of entries, tasks created, thoughts saved, observations.
Return ONLY RAW HTML. NO markdown. NO explanation. Start with <!DOCTYPE html>."
```
