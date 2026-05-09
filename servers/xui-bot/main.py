import asyncio
import logging
from logging.handlers import RotatingFileHandler

import aiohttp
from aiohttp import web

from aiogram import Bot, Dispatcher, BaseMiddleware
from fsm_storage import SQLiteStorage
from aiogram.types import TelegramObject

from config import BOT_TOKEN, ADMIN_ID
import database

from handlers import start, create_user, stats, admin, admin_settings, search

SUB_BASE = "https://white.theredhat.su:8888/sub"


async def _redirect_happ(request: web.Request) -> web.Response:
    uuid = request.match_info["uuid"]
    name = request.rel_url.query.get("name", "VPN")
    sub_url = f"{SUB_BASE}/{uuid}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://crypto.happ.su/api-v2.php",
                json={"url": sub_url, "name": name},
                timeout=aiohttp.ClientTimeout(total=6),
            ) as resp:
                data = await resp.json(content_type=None)
                happ_link = data.get("encrypted_link")
        if happ_link:
            raise web.HTTPFound(location=happ_link)
    except web.HTTPFound:
        raise
    except Exception:
        pass
    raise web.HTTPBadGateway()


async def start_redirect_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/r/happ/{uuid}", _redirect_happ)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8090)
    await site.start()
    return runner


class AdminOnlyMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user and user.id != ADMIN_ID:
            return  # молча игнорируем
        return await handler(event, data)


def setup_logging():
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)

    logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    await database.init_db()
    logger.info("База данных инициализирована")

    await start_redirect_server()
    logger.info("Redirect server started on :8090")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=SQLiteStorage("data/fsm.db"))
    dp.update.middleware(AdminOnlyMiddleware())

    dp.include_router(start.router)
    dp.include_router(create_user.router)
    dp.include_router(stats.router)
    dp.include_router(admin.router)
    dp.include_router(admin_settings.router)
    dp.include_router(search.router)

    logger.info("Бот запускается...")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
