import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, MenuButtonWebApp
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "50949302"))
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://example.com")

logging.basicConfig(level=logging.INFO)


async def post_init(application):
    """Устанавливаем кнопку меню — Mini App открывается одним тапом без /start"""
    await application.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="📡 Монитор",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    )


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Доступ запрещён.")
        return

    keyboard = [[
        InlineKeyboardButton(
            "📡 Открыть монитор",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    ]]
    await update.message.reply_text(
        "📡 *Router Monitor*\n\nНажми кнопку меню слева или кнопку ниже.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Быстрый статус без открытия Mini App"""
    if update.effective_user.id != ADMIN_ID:
        return
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{MINIAPP_URL}/api/devices", timeout=10)
            data = r.json()
        text = (
            f"📡 *Статус роутеров*\n\n"
            f"Всего: {data['total']}\n"
            f"🟢 Онлайн: {data['online']}\n"
            f"⚫ Офлайн: {data['offline']}"
        )
    except Exception as e:
        text = f"❌ Ошибка: {e}"

    await update.message.reply_text(text, parse_mode="Markdown")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    print("Бот запущен...")
    app.run_polling()
