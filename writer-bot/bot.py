#!/usr/bin/env python3
"""Writer bot — собирает статьи в стиле Неверова из голосовых/текстовых заметок."""
import asyncio
import logging
import os
import re
import tempfile
from pathlib import Path

import subprocess

import httpx
from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))
ELEVEN_API_KEY = os.environ.get("ELEVEN_API_KEY", "")

# ─── Состояние пользователя ────────────────────────────────────────────────────
# "noting"    — копим заметки, любой текст = новая заметка
# "reviewing" — работаем с черновиком, текст = инструкция правки

notes: dict[int, list[str]] = {}        # сырые заметки
current_draft: dict[int, str] = {}      # текущий черновик (обновляется при правке)
last_article: dict[int, str] = {}       # последняя финальная статья для озвучки
user_state: dict[int, str] = {}         # "noting" | "reviewing"


def get_state(uid: int) -> str:
    return user_state.get(uid, "noting")


def set_state(uid: int, state: str):
    user_state[uid] = state


def user_notes(uid: int) -> list[str]:
    return notes.get(uid, [])


def add_note(uid: int, text: str) -> int:
    if uid not in notes:
        notes[uid] = []
    notes[uid].append(text.strip())
    return len(notes[uid])


def reset_all(uid: int):
    notes[uid] = []
    current_draft.pop(uid, None)
    last_article.pop(uid, None)
    set_state(uid, "noting")


# ─── Постоянная клавиатура ─────────────────────────────────────────────────────

BTN_NOTES = "💭 МЫСЛЬ"
BTN_DRAFT = "📝 ЧЕРНОВИК"
BTN_TTS   = "🔊 ОЗВУЧИТЬ"
BTN_RESET = "🗑️ СБРОС"

MAIN_KB = ReplyKeyboardMarkup(
    [
        [KeyboardButton(BTN_NOTES), KeyboardButton(BTN_DRAFT), KeyboardButton(BTN_TTS)],
        [KeyboardButton(BTN_RESET)],
    ],
    resize_keyboard=True,
    is_persistent=True,
)

# ─── Инлайн-клавиатуры ────────────────────────────────────────────────────────

def draft_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✏️ ДОПОЛНИТЬ", callback_data="add_more"),
        InlineKeyboardButton("✅ ФИНАЛ", callback_data="final"),
    ]])


def final_kb() -> InlineKeyboardMarkup:
    row1 = []
    if ELEVEN_API_KEY:
        row1.append(InlineKeyboardButton("🔊 Озвучить", callback_data="tts"))
    row2 = [InlineKeyboardButton("🆕 НОВОЕ", callback_data="new_article")]
    return InlineKeyboardMarkup([row1, row2] if row1 else [row2])


def finalize_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ ФИНАЛ", callback_data="final"),
    ]])


# ─── Deepgram транскрибация ────────────────────────────────────────────────────

def transcribe(file_path: str) -> str:
    with open(file_path, "rb") as f:
        audio_data = f.read()
    response = httpx.post(
        "https://api.deepgram.com/v1/listen",
        params={"model": "nova-2", "language": "ru", "smart_format": "true", "punctuate": "true"},
        headers={"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": "audio/ogg"},
        content=audio_data,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]


# ─── Claude ───────────────────────────────────────────────────────────────────

STYLE_SYSTEM = """Ты пишешь в стиле Василия Неверова — автора ТГ-канала и блога на Дзене.

Стиль:
• Структура: крюк → личный контекст → проблема → разбор → максима
• Первое лицо, самоирония ("зануда", "граммар-наци")
• Театральность: CAPS, восклицания, многоточия
• Прямое обращение к читателю ("давайте разберём", "я вам скажу")
• Цифровая конкретность (56 хостелов, 31 страна, 1 100 ₽)
• Честная критика любимого — хвалит и находит минус
• Провокационный заголовок с неожиданным поворотом
• Баланс цинизма и оптимизма
• Финальная максима адаптирована к теме"""


def ask_claude(prompt: str) -> str:
    """Вызов Claude Code CLI через subprocess (использует Pro-подписку)."""
    env = os.environ.copy()
    env["HOME"] = "/home/writer"
    # Убираем API ключ — иначе claude использует его вместо OAuth
    env.pop("ANTHROPIC_API_KEY", None)
    result = subprocess.run(
        ["claude", "-p", prompt, "--dangerously-skip-permissions"],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip() or "claude CLI error"
        logger.error("claude exit=%s stdout=%r stderr=%r", result.returncode, result.stdout[:200], result.stderr[:200])
        raise RuntimeError(err)
    return result.stdout.strip()


def build_draft(uid: int) -> str:
    raw = "\n\n".join(f"{i+1}. {n}" for i, n in enumerate(user_notes(uid)))
    return ask_claude(f"""{STYLE_SYSTEM}

Мои сырые заметки:

{raw}

Собери ЧЕРНОВИК статьи. Сохрани все мысли, свяжи в нарратив, добавь структуру.
Это черновик для проверки — не полируй до конца. Один вариант текста.""")


def revise_draft(uid: int, instruction: str) -> str:
    draft = current_draft.get(uid, "")

    low = instruction.lower().strip()
    if low.startswith("исправь") or low.startswith("исправи"):
        action = "ИСПРАВЬ в черновике"
        content = instruction.split(None, 1)[1] if " " in instruction else instruction
    elif low.startswith("дополни"):
        action = "ДОПОЛНИ черновик"
        content = instruction.split(None, 1)[1] if " " in instruction else instruction
    else:
        action = "Измени черновик согласно инструкции"
        content = instruction

    return ask_claude(f"""{STYLE_SYSTEM}

Вот текущий черновик:

{draft}

{action}: {content}

Верни только обновлённый черновик, без комментариев.""")


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def build_final(uid: int) -> str:
    draft = current_draft.get(uid, "")
    return ask_claude(f"""{STYLE_SYSTEM}

Вот черновик статьи:

{draft}

Напиши финальную версию для TELEGRAM-КАНАЛА в HTML-разметке.

ДЛИНА: 3–4 абзаца, 1600–1900 символов текста без тегов.

ЭМОДЗИ: обязательно по смыслу в каждом абзаце — не декоративно, а точно в тему. Минимум 4–6 эмодзи на весь текст.

ФОРМАТИРОВАНИЕ — используй HTML-теги по смыслу:
• Первые 3–6 слов каждого абзаца оберни в <b>...</b>
• Сильную мысль, цитату или наблюдение — в <blockquote>...</blockquote>
• Для иронии (зачёркнутое "старое" мнение): <s>устаревшее</s> актуальное
• Для интриги или неожиданной концовки: <tg-spoiler>текст</tg-spoiler>
• В конце — вопрос или призыв + 3–5 хэштегов
• Никаких подзаголовков, единый текст

ВАЖНО: верни только готовый HTML-текст, без пояснений и без markdown-блоков.""")


# ─── ElevenLabs TTS ───────────────────────────────────────────────────────────

ELEVEN_VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"  # Liam — мужской, хорошо читает русский

def tts_to_mp3(text: str) -> bytes:
    response = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}",
        headers={"xi-api-key": ELEVEN_API_KEY, "Content-Type": "application/json"},
        json={"text": text, "model_id": "eleven_multilingual_v2",
              "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
        timeout=60,
    )
    response.raise_for_status()
    return response.content


# ─── Хендлеры ─────────────────────────────────────────────────────────────────

def allowed(update: Update) -> bool:
    if not ALLOWED_USER_ID:
        return True
    return update.effective_user.id == ALLOWED_USER_ID


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✍️ *Бот-писатель*\n\n"
        "Отправляй голосовые или текстовые заметки — накоплю за день.\n\n"
        "💭 МЫСЛЬ — посмотреть накопленные заметки\n"
        "📝 ЧЕРНОВИК — собрать черновик из заметок\n"
        "🔊 ОЗВУЧИТЬ — прочитать последнюю статью вслух",
        parse_mode="Markdown",
        reply_markup=MAIN_KB,
    )


async def show_notes(update: Update):
    uid = update.effective_user.id
    saved = user_notes(uid)
    if not saved:
        await update.message.reply_text("📭 Заметок пока нет — отправляй текст или голосовое")
        return
    lines = [f"📝 *Заметок: {len(saved)}*\n"]
    for i, note in enumerate(saved, 1):
        preview = note[:200] + "…" if len(note) > 200 else note
        lines.append(f"*{i}.* {preview}")
    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")


async def do_draft(update: Update):
    uid = update.effective_user.id
    saved = user_notes(uid)
    if not saved:
        await update.message.reply_text("📭 Нет заметок. Отправь текст или голосовое.")
        return

    msg = await update.message.reply_text(f"✍️ Собираю черновик из {len(saved)} заметок…")
    try:
        draft = await asyncio.to_thread(build_draft, uid)
    except Exception as e:
        logger.exception("Draft error")
        await msg.edit_text(f"❌ Ошибка: {e}")
        return

    current_draft[uid] = draft
    set_state(uid, "reviewing")
    await msg.delete()
    await update.message.reply_text(draft, reply_markup=draft_kb())


async def do_tts(update: Update):
    uid = update.effective_user.id
    text = last_article.get(uid)
    if not text:
        await update.message.reply_text("📭 Нет статьи для озвучки — сначала сделай финал")
        return
    if not ELEVEN_API_KEY:
        await update.message.reply_text("⚙️ ElevenLabs ключ не настроен")
        return
    msg = await update.message.reply_text("🔊 Озвучиваю…")
    try:
        audio = await asyncio.to_thread(tts_to_mp3, strip_html(text))
    except Exception as e:
        logger.exception("TTS error")
        await msg.edit_text(f"❌ Ошибка озвучки: {e}")
        return
    await msg.delete()
    await update.message.reply_audio(audio, filename="article.mp3")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return
    uid = update.effective_user.id
    text = update.message.text

    # Кнопки постоянной клавиатуры — всегда перехватываем первыми
    if text == BTN_NOTES:
        await show_notes(update)
    elif text == BTN_DRAFT:
        await do_draft(update)
    elif text == BTN_TTS:
        await do_tts(update)
    elif text == BTN_RESET:
        await update.message.reply_text(
            "Сбросить всё и начать сначала?",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Да, сброс ❌", callback_data="confirm_reset"),
                InlineKeyboardButton("Отмена", callback_data="cancel_reset"),
            ]]),
        )

    # В режиме работы с черновиком — текст = инструкция правки
    elif get_state(uid) == "reviewing":
        msg = await update.message.reply_text("✏️ Правлю…")
        try:
            revised = await asyncio.to_thread(revise_draft, uid, text)
        except Exception as e:
            logger.exception("Revise error")
            await msg.edit_text(f"❌ Ошибка: {e}")
            return
        current_draft[uid] = revised
        await msg.delete()
        await update.message.reply_text(
            f"{revised}\n\n—\nИзменил. Финализируем?",
            reply_markup=finalize_kb(),
        )

    # В режиме накопления — текст = новая заметка
    else:
        n = add_note(uid, text)
        await update.message.reply_text(f"✅ #{n}")


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return
    uid = update.effective_user.id
    progress = await update.message.reply_text("🎤 Транскрибирую…")
    voice_file = await context.bot.get_file(update.message.voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        await voice_file.download_to_drive(tmp_path)
        transcript = await asyncio.to_thread(transcribe, tmp_path)
        # Голосовое в режиме reviewing — тоже правка
        if get_state(uid) == "reviewing":
            msg2 = await progress.edit_text(f"✏️ Правлю по голосовой: _{transcript}_…",
                                            parse_mode="Markdown")
            try:
                revised = await asyncio.to_thread(revise_draft, uid, transcript)
            except Exception as e:
                logger.exception("Revise error")
                await msg2.edit_text(f"❌ Ошибка: {e}")
                return
            current_draft[uid] = revised
            await msg2.delete()
            await update.message.reply_text(
                f"{revised}\n\n—\nИзменил. Финализируем?",
                reply_markup=finalize_kb(),
            )
        else:
            n = add_note(uid, transcript)
            await progress.edit_text(f"✅ #{n}: _{transcript}_", parse_mode="Markdown")
    except Exception as e:
        logger.exception("Voice error")
        await progress.edit_text(f"❌ Ошибка транскрибации: {e}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        return
    reset_all(update.effective_user.id)
    await update.message.reply_text("🗑️ Заметки очищены")


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not allowed(update):
        return

    uid = query.from_user.id
    data = query.data

    if data == "add_more":
        # Убираем кнопку ДОПОЛНИТЬ, оставляем только ФИНАЛ
        await query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ ФИНАЛ", callback_data="final"),
            ]])
        )
        set_state(uid, "noting")
        await query.message.reply_text(
            "Добавляй мысли или голосовые.\nКогда готово — нажми 📝 ЧЕРНОВИК снова."
        )

    elif data == "final":
        if uid not in current_draft:
            await query.answer("Нет черновика", show_alert=True)
            return
        msg = await query.message.reply_text("✍️ Финализирую…")
        try:
            final = await asyncio.to_thread(build_final, uid)
        except Exception as e:
            logger.exception("Final error")
            await msg.edit_text(f"❌ Ошибка: {e}")
            return
        last_article[uid] = final
        set_state(uid, "noting")
        await msg.delete()
        await query.message.reply_text(final, reply_markup=final_kb(), parse_mode="HTML")

    elif data == "new_article":
        await query.message.reply_text(
            "Стереть все заметки и начать заново?",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Точно ❌", callback_data="confirm_new"),
                InlineKeyboardButton("Отмена", callback_data="cancel_new"),
            ]]),
        )

    elif data == "confirm_new":
        reset_all(uid)
        await query.message.edit_text("✅ Готово. Жду новые мысли 👂")

    elif data == "cancel_new":
        await query.message.delete()

    elif data == "confirm_reset":
        reset_all(uid)
        await query.message.edit_text("✅ Сброшено. Жду новые мысли 👂")

    elif data == "cancel_reset":
        await query.message.delete()

    elif data == "tts":
        text = last_article.get(uid)
        if not text:
            await query.answer("Нет статьи для озвучки", show_alert=True)
            return
        msg = await query.message.reply_text("🔊 Озвучиваю…")
        try:
            audio = await asyncio.to_thread(tts_to_mp3, strip_html(text))
        except Exception as e:
            logger.exception("TTS error")
            await msg.edit_text(f"❌ Ошибка озвучки: {e}")
            return
        await msg.delete()
        await query.message.reply_audio(audio, filename="article.mp3")



# ─── Запуск ────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(CallbackQueryHandler(on_callback))

    logger.info("Writer bot started")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
