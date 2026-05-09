"""
ФИКС для process.py — отправка HTML отчёта как файла

Добавить в конец cmd_process() после отправки текстового отчёта
"""

import re
from pathlib import Path
from aiogram.types import FSInputFile, BufferedInputFile

# ... после: await status_msg.edit_text(report, parse_mode="HTML")

# === НАЧАЛО ФИКСА ===
# Ищем путь к HTML файлу или сохраняем report в файл

# Вариант 1: process.sh создаёт HTML файл и выводит его путь
html_path = None
output_text = result.get("output", "")

# Ищем REPORT_PATH= в stdout
path_match = re.search(r'REPORT_PATH=(\S+)', output_text)
if path_match:
    html_path = Path(path_match.group(1))

# Вариант 2: стандартный путь к отчёту (process.sh должен сохранить туда)
if not html_path or not html_path.exists():
    today_str = date.today().isoformat()
    default_paths = [
        Path(f"/home/sbrain/sbrain/vault/reports/daily_{today_str}.html"),
        Path(f"/home/sbrain/sbrain/reports/daily_{today_str}.html"),
        Path(settings.vault_path) / "reports" / f"daily_{today_str}.html",
    ]
    for p in default_paths:
        if p.exists():
            html_path = p
            break

# Если файл не найден, но у нас есть report текст — сохраним его
if not html_path and report:
    try:
        today_str = date.today().isoformat()
        reports_dir = Path(settings.vault_path) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        html_path = reports_dir / f"daily_{today_str}.html"
        html_path.write_text(report, encoding="utf-8")
        logger.info(f"Saved HTML report to {html_path}")
    except Exception as e:
        logger.error(f"Failed to save HTML: {e}")

# Отправляем файл
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
    logger.warning("HTML report not found or not created")
# === КОНЕЦ ФИКСА ===


"""
АЛЬТЕРНАТИВНЫЙ ФИКС — если report текст велик, отправляем как BufferedInputFile:

if report and len(report) > 4000:  # Telegram limit for messages
    from aiogram.types import BufferedInputFile
    html_bytes = report.encode("utf-8")
    await message.answer_document(
        BufferedInputFile(html_bytes, filename=f"daily_{date.today().isoformat()}.html"),
        caption="📊 Полный отчёт обработки"
    )
"""


"""
ПОЛНЫЙ ОБНОВЛЁННЫЙ HANDLER process.py:
"""

import asyncio
import logging
import os
import re
from datetime import date
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from d_brain.bot.formatters import format_process_report
from d_brain.services.finance_tracker import read_finance_snapshot
from d_brain.bot.handlers.finance import _parse_balances, _calc_today_net
from d_brain.config import get_settings
from d_brain.services.git import VaultGit

router = Router(name="process")
logger = logging.getLogger(__name__)

PROCESS_TIMEOUT = 600  # 10 minutes


def _progress_bar(pct: int, width: int = 10) -> str:
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _estimate_pct(elapsed: int) -> int:
    return min(99, int(elapsed / (elapsed + 90) * 100))


@router.message(Command("process"))
async def cmd_process(message: Message) -> None:
    """Handle /process command - trigger FAST processing via process.sh."""
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info("Process command triggered by user %s (FAST mode)", user_id)

    status_msg = await message.answer("⏳ Запускаю быструю обработку (3 фазы)...")

    settings = get_settings()
    vault_path = Path(settings.vault_path)
    project_dir = vault_path.parent
    process_script = project_dir / "scripts" / "process.sh"

    async def run_process_with_watchdog() -> dict:
        env = os.environ.copy()
        env["PATH"] = f"{Path.home()}/.local/bin:{env.get('PATH', '')}"
        env["TELEGRAM_BOT_TOKEN"] = settings.telegram_bot_token
        env["ALLOWED_USER_IDS"] = str(settings.allowed_user_ids[0] if settings.allowed_user_ids else "")
        env["TZ"] = "Europe/Moscow"

        proc = await asyncio.create_subprocess_exec(
            "bash", str(process_script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(project_dir),
            env=env
        )

        elapsed = 0
        phase = "CAPTURE"

        async def update_progress():
            nonlocal elapsed, phase
            while True:
                await asyncio.sleep(10)
                elapsed += 10
                pct = _estimate_pct(elapsed)
                bar = _progress_bar(pct)
                mins = elapsed // 60
                secs = elapsed % 60

                if elapsed > 60:
                    phase = "EXECUTE" if elapsed < 180 else "REFLECT"

                try:
                    await status_msg.edit_text(
                        f"⏳ Фаза {phase}...\n{bar} {pct}%\n{mins}м {secs}с"
                    )
                except Exception:
                    pass

        progress_task = asyncio.create_task(update_progress())

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=PROCESS_TIMEOUT
            )

            output = stdout.decode() if stdout else ""

            return {
                "success": proc.returncode == 0,
                "output": output,
                "elapsed": elapsed,
                "phases_completed": "CAPTURE → EXECUTE → REFLECT"
            }

        except asyncio.TimeoutError:
            logger.error("Process.sh timeout after %s seconds", PROCESS_TIMEOUT)
            try:
                proc.kill()
                await proc.wait()
            except:
                pass
            return {
                "error": f"Timeout after {PROCESS_TIMEOUT//60} minutes",
                "timeout": True,
                "elapsed": elapsed
            }
        finally:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

    result = await run_process_with_watchdog()

    if result.get("success"):
        output_text = result.get("output", "")

        # Extract report from output
        report = ""
        if "=== Claude output ===" in output_text:
            report = output_text.split("=== Claude output ===")[-1].split("====================")[0].strip()
        else:
            # Try to find HTML report
            report = output_text.strip()

        if not report:
            report = "✅ <b>Обработка завершена!</b>\n\n3 фазы выполнены:\n• CAPTURE — классификация\n• EXECUTE — задачи созданы\n• REFLECT — отчет сгенерирован"

        await status_msg.edit_text(report[:4000], parse_mode="HTML")

        # === НАЧАЛО ИЗМЕНЕНИЙ: Отправка HTML файла ===
        # Ищем или сохраняем HTML файл
        html_path = None
        today_str = date.today().isoformat()

        # Ищем REPORT_PATH в stdout
        path_match = re.search(r'REPORT_PATH=(\S+\.html)', output_text)
        if path_match:
            html_path = Path(path_match.group(1))

        # Проверяем стандартные пути
        if not html_path or not html_path.exists():
            default_paths = [
                project_dir / "reports" / f"daily_{today_str}.html",
                vault_path / "reports" / f"daily_{today_str}.html",
                Path(f"/home/sbrain/sbrain/vault/reports/daily_{today_str}.html"),
            ]
            for p in default_paths:
                if p.exists():
                    html_path = p
                    break

        # Если файл не найден, сохраняем report
        if not html_path and report:
            try:
                reports_dir = vault_path / "reports"
                reports_dir.mkdir(parents=True, exist_ok=True)
                html_path = reports_dir / f"daily_{today_str}.html"
                html_path.write_text(report, encoding="utf-8")
                logger.info(f"Saved HTML report to {html_path}")
            except Exception as e:
                logger.error(f"Failed to save HTML: {e}")

        # Отправляем файл
        if html_path and html_path.exists():
            try:
                await message.answer_document(
                    FSInputFile(str(html_path)),
                    caption="📊 Полный отчёт обработки"
                )
                logger.info(f"Sent HTML report: {html_path}")
            except Exception as e:
                logger.error(f"Failed to send document: {e}")
        # === КОНЕЦ ИЗМЕНЕНИЙ ===

    else:
        error = result.get("error", "Unknown error")
        await status_msg.edit_text(f"⚠️ <b>Ошибка обработки:</b>\n<code>{error}</code>", parse_mode="HTML")

    # Finance summary
    try:
        block = read_finance_snapshot(settings.vault_path)
        if block:
            balances = _parse_balances(block)
            total = sum(v for _, v in balances)
            today_net = _calc_today_net(block)
            prev = total - today_net
            net_sign = "+" if today_net >= 0 else ""
            tf = f"{total:,}".replace(",", " ")
            pf = f"{prev:,}".replace(",", " ")
            nf = f"{net_sign}{today_net:,}".replace(",", " ")
            await message.answer(
                f"💼 <b>{tf} ₽</b>  <i>(было {pf} ₽, сегодня {nf} ₽)</i>",
                parse_mode="HTML"
            )
    except Exception:
        pass
