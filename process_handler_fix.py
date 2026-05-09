"""
ФИКС для process.py — отправка HTML отчёта после process.sh

Добавить в конец функции cmd_process() после завершения process.sh
"""

import asyncio
import re
from pathlib import Path
from aiogram.types import FSInputFile

# ... существующий код до конца process.sh ...

# После: stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)

# === НАЧАЛО ФИКСА ===
# Ищем путь к HTML отчёту в stdout
html_path = None
output_text = stdout.decode() if stdout else ""

# Вариант 1: process.sh выводит REPORT_PATH=/path/to/file.html
path_match = re.search(r'REPORT_PATH=(\S+)', output_text)
if path_match:
    html_path = Path(path_match.group(1))

# Вариант 2: process.sh выводит путь к HTML явно
if not html_path:
    html_match = re.search(r'(/[^\s]+\.html)', output_text)
    if html_match:
        html_path = Path(html_match.group(1))

# Вариант 3: стандартный путь reports/daily_YYYY-MM-DD.html
today_str = date.today().isoformat()
default_path = Path(f"/home/sbrain/sbrain/vault/reports/daily_{today_str}.html")
if not html_path and default_path.exists():
    html_path = default_path

# Проверяем что файл существует и отправляем
if html_path and html_path.exists():
    try:
        await message.answer_document(
            FSInputFile(str(html_path)),
            caption="📊 Полный отчёт обработки"
        )
    except Exception as e:
        logger.error(f"Failed to send HTML report: {e}")
        await message.answer(f"⚠️ Не удалось отправить отчёт: {e}")
else:
    logger.warning(f"HTML report not found. Path tried: {html_path}")
    await message.answer("⚠️ HTML отчёт не найден, но обработка завершена успешно.")

# === КОНЕЦ ФИКСА ===


"""
АЛЬТЕРНАТИВНЫЙ ФИКС — если process.sh не выводит путь явно:

Добавить в process.sh в конец фазы REFLECT:

echo "REPORT_PATH=$REPORT_PATH"

Где $REPORT_PATH — переменная с путем к сгенерированному HTML файлу.
"""

"""
ПОЛНЫЙ ОБНОВЛЁННЫЙ HANDLER (для замены в process.py):
"""

async def cmd_process(message: Message) -> None:
    """Handle /process command - trigger Claude processing via process.sh."""
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info("Process command triggered by user %s", user_id)

    status_msg = await message.answer("⏳ Запускаю обработку...")

    settings = get_settings()
    process_script = Path(settings.vault_path) / "scripts" / "process.sh"

    # Запускаем process.sh
    proc = await asyncio.create_subprocess_exec(
        "bash", str(process_script),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
    except asyncio.TimeoutError:
        await status_msg.edit_text("❌ Таймаут обработки (>10 мин)")
        return

    output_text = stdout.decode() if stdout else ""
    error_text = stderr.decode() if stderr else ""

    # Парсим результат
    if proc.returncode != 0:
        await status_msg.edit_text(f"❌ Ошибка обработки:\n<pre>{error_text[:500]}</pre>", parse_mode="HTML")
        return

    # Ищем HTML отчёт
    html_path = None
    today_str = date.today().isoformat()

    # Вариант 1: из stdout REPORT_PATH=
    path_match = re.search(r'REPORT_PATH=(\S+)', output_text)
    if path_match:
        html_path = Path(path_match.group(1))

    # Вариант 2: стандартный путь
    if not html_path or not html_path.exists():
        default_paths = [
            Path(f"/home/sbrain/sbrain/vault/reports/daily_{today_str}.html"),
            Path(settings.vault_path) / "reports" / f"daily_{today_str}.html",
            Path(settings.vault_path) / "output" / f"daily_{today_str}.html",
        ]
        for p in default_paths:
            if p.exists():
                html_path = p
                break

    # Формируем текст ответа
    success_text = "✅ Обработка завершена!\n\n3 фазы выполнены:\n• CAPTURE — классификация\n• EXECUTE — задачи созданы\n• REFLECT — отчет сгенерирован"

    await status_msg.edit_text(success_text)

    # Отправляем HTML файл
    if html_path and html_path.exists():
        try:
            await message.answer_document(
                FSInputFile(str(html_path)),
                caption="📊 Полный отчёт обработки"
            )
            logger.info(f"Sent HTML report: {html_path}")
        except Exception as e:
            logger.error(f"Failed to send document: {e}")
            await message.answer(f"⚠️ Не удалось отправить файл: {e}")
    else:
        logger.warning(f"HTML report not found. Searched paths including: {default_paths[0] if 'default_paths' in locals() else 'N/A'}")
        await message.answer("⚠️ HTML файл отчёта не найден. Проверьте директорию reports/")
