#!/bin/bash
# ============================================================================
# d-brain process.sh — 3-фазная обработка через DeepSeek API
# Сервер: 144.31.244.181, проект: /home/sbrain/sbrain
# Версия: 2026-05-12 (fixed: file contents inlined into prompts)
# ============================================================================
set -euo pipefail

# ── Конфигурация ──────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/.."
VAULT_DIR="${PROJECT_DIR}/vault"
SESSION_DIR="${VAULT_DIR}/.session"
DEEPSEEK_CLI="${SCRIPT_DIR}/deepseek_cli.py"
PARSE_JSON="${SCRIPT_DIR}/parse_json.py"
TODAY="${1:-$(TZ=Europe/Moscow date +%Y-%m-%d)}"
YESTERDAY="$(TZ=Europe/Moscow date -d "yesterday" +%Y-%m-%d)"

mkdir -p "${SESSION_DIR}"

# ── ORIENT: определить какой daily-файл обрабатывать ──────────────────────
DAILY_REL="daily/${TODAY}.md"
DAILY_FILE="${VAULT_DIR}/${DAILY_REL}"

if [ ! -f "${DAILY_FILE}" ] || [ "$(wc -c < "${DAILY_FILE}")" -lt 50 ]; then
    YESTERDAY_FILE="${VAULT_DIR}/daily/${YESTERDAY}.md"
    if [ -f "${YESTERDAY_FILE}" ] && [ "$(wc -c < "${YESTERDAY_FILE}")" -ge 50 ]; then
        DAILY_REL="daily/${YESTERDAY}.md"
        DAILY_FILE="${YESTERDAY_FILE}"
        echo "[ORIENT] Using yesterday's file: ${DAILY_REL}"
    else
        echo "[ORIENT] No entries to process. Exiting."
        exit 0
    fi
fi

echo "[ORIENT] Processing: ${DAILY_REL} ($(wc -l < "${DAILY_FILE}") lines)"

# ── Phase 1: CAPTURE — классификация записей ──────────────────────────────
echo "[CAPTURE] Starting Phase 1..."
DAILY_CONTENT=$(cat "${DAILY_FILE}")

CAPTURE_PROMPT="Today is ${TODAY}. Below is the content of ${DAILY_REL}:

\`\`\`
${DAILY_CONTENT}
\`\`\`

For each entry (## HH:MM [type] block), classify it as one of: task, idea, reflection, learning, project, crm_update, finance, skip.

Return ONLY valid JSON with this exact structure:
{
  \"date\": \"${TODAY}\",
  \"entries\": [
    {
      \"time\": \"HH:MM\",
      \"type\": \"voice|text|photo\",
      \"content\": \"original entry text\",
      \"classification\": \"task|idea|reflection|learning|project|crm_update|finance|skip\",
      \"task_content\": \"if task, what to do\",
      \"task_priority\": 1-4,
      \"entities\": []
    }
  ],
  \"stats\": {\"total_entries\": 0, \"tasks\": 0, \"thoughts\": 0, \"skipped\": 0}
}

NO explanation. NO markdown. ONLY JSON."

CAPTURE_RAW=$(echo "${CAPTURE_PROMPT}" | python3 "${DEEPSEEK_CLI}" 2>&1)
CAPTURE_JSON=$(echo "${CAPTURE_RAW}" | python3 "${PARSE_JSON}")
echo "${CAPTURE_JSON}" > "${SESSION_DIR}/capture.json"
echo "[CAPTURE] Done: $(python3 -c "import json; d=json.load(open('${SESSION_DIR}/capture.json')); print(d.get('stats',{}))" 2>/dev/null || echo 'ok')"

# ── Phase 2: EXECUTE — создание задач/мыслей ──────────────────────────────
echo "[EXECUTE] Starting Phase 2..."
CAPTURE_CONTENT=$(cat "${SESSION_DIR}/capture.json")

EXECUTE_PROMPT="Today is ${TODAY}. Below is the capture.json with classified entries:

\`\`\`json
${CAPTURE_CONTENT}
\`\`\`

For each entry:
- If classification is 'task': create a task entry with content from task_content
- If classification is 'idea|reflection|learning|project': create a thought entry
- If classification is 'finance': note it for the report

Return ONLY valid JSON with this exact structure:
{
  \"tasks_created\": [{\"content\": \"task text\", \"priority\": 2}],
  \"thoughts_saved\": [
    {\"title\": \"thought title\", \"category\": \"ideas|learnings|reflections|projects\", \"content\": \"full thought text\"}
  ],
  \"observations\": [\"key observation from today\"]
}

NO explanation. NO markdown. ONLY JSON."

EXECUTE_RAW=$(echo "${EXECUTE_PROMPT}" | python3 "${DEEPSEEK_CLI}" 2>&1)
EXECUTE_JSON=$(echo "${EXECUTE_RAW}" | python3 "${PARSE_JSON}")
echo "${EXECUTE_JSON}" > "${SESSION_DIR}/execute.json"
echo "[EXECUTE] Done"

# ── Phase 3: REFLECT — HTML-отчёт ─────────────────────────────────────────
echo "[REFLECT] Starting Phase 3..."
EXECUTE_CONTENT=$(cat "${SESSION_DIR}/execute.json")

# Собрать контекст: MEMORY.md (балансы, продажи, дебиторка) + последние daily
MEMORY_CONTENT=""
if [ -f "${VAULT_DIR}/MEMORY.md" ]; then
    MEMORY_CONTENT=$(cat "${VAULT_DIR}/MEMORY.md")
fi

RECENT_DAILY=""
for f in $(ls -t "${VAULT_DIR}/daily/"*.md 2>/dev/null | head -7); do
    RECENT_DAILY="${RECENT_DAILY}
--- $(basename "$f") ---
$(head -100 "$f")
"
done

REFLECT_PROMPT="Today is ${TODAY}. Generate a daily report in Telegram HTML format.

=== MEMORY (balances, sales, debtors, weight history) ===
${MEMORY_CONTENT}

=== RECENT DAILY ENTRIES (last 7 days) ===
${RECENT_DAILY}

=== CAPTURE data (today's classified entries) ===

CAPTURE data (classified entries):
\`\`\`json
${CAPTURE_CONTENT}
\`\`\`

EXECUTE data (tasks and thoughts):
\`\`\`json
${EXECUTE_CONTENT}
\`\`\`

Generate a Telegram HTML report with these sections:

1. 📊 Header: \"Обработка за ${TODAY}\"
2. 📝 Записи: list each entry with classification and amount if finance
3. 🛜 ПРОДАЖИ РОУТЕРОВ: cumulative by month (Март/Апрель/Май)
4. 📱 VPN В ТЕЛЕФОН: cumulative by month
5. 💳 БАЛАНСЫ КАРТ: 🟢Сбер, 🟡Т-банк, 🔴Яндекс, 🟣WB Банк, ⚪Нал, 💵Нал $, 💼ИТОГО
6. 👤 АНТОН ПОТРАТИЛ: spent/total limit
7. 📋 ДЕБИТОРКА: list of debtors
8. ⚖️ ВЕС: recent weight entries with dynamics
9. 💰 Итог дня: income/expenses summary

Use HTML tags: <b>bold</b>, <i>italic</i>, <code>code</code>.
Use emoji as shown.
Return ONLY raw HTML. NO markdown. NO explanation. Start with the header."

REFLECT_RAW=$(echo "${REFLECT_PROMPT}" | python3 "${DEEPSEEK_CLI}" 2>&1)
REFLECT_HTML=$(echo "${REFLECT_RAW}" | python3 -c "import sys; t=sys.stdin.read(); t=t[t.find('<b>'):t.rfind('</i>')+4] if '<b>' in t and '</i>' in t else t; print(t)" 2>/dev/null || echo "${REFLECT_RAW}")

REPORT_FILE="${VAULT_DIR}/reports/daily_${TODAY}.html"
mkdir -p "$(dirname "${REPORT_FILE}")"
echo "${REFLECT_HTML}" > "${REPORT_FILE}"
echo "[REFLECT] Report saved to ${REPORT_FILE}"

# ── Вывод для bot handler ─────────────────────────────────────────────────
echo "CAPTURE_COMPLETE=true"
echo "EXECUTE_COMPLETE=true"
echo "REPORT_PATH=${REPORT_FILE}"
echo "DAILY_FILE=${DAILY_REL}"

exit 0
