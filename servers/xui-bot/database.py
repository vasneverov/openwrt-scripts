import aiosqlite
import os
from typing import Optional

DB_PATH = os.getenv("DB_PATH", "./data/bot.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                key          TEXT UNIQUE NOT NULL,
                button_name  TEXT NOT NULL,
                country_flag TEXT NOT NULL,
                url          TEXT NOT NULL,
                username     TEXT NOT NULL,
                password     TEXT NOT NULL,
                inbound_id   INTEGER NOT NULL,
                is_active    BOOLEAN DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        defaults = [
            ("profile_prefix",    ""),
            ("profile_postfix",   ""),
            ("message_footer",    "Вставь ссылку в приложение Happ"),
            ("app_name",          "Happ"),
            ("app_link_ios",      "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973"),
            ("app_link_android",  "https://play.google.com/store/apps/details?id=com.happproxy"),
            ("default_username",  "ad"),
            ("default_password",  "56"),
        ]
        for key, value in defaults:
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        await db.commit()


async def get_all_servers() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE is_active = 1 ORDER BY id"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_server(key: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE key = ? AND is_active = 1", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def add_server(
    key: str,
    button_name: str,
    country_flag: str,
    url: str,
    username: str,
    password: str,
    inbound_id: int,
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO servers (key, button_name, country_flag, url, username, password, inbound_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (key, button_name, country_flag, url, username, password, inbound_id),
        )
        await db.commit()


async def update_server_inbound(key: str, inbound_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE servers SET inbound_id = ? WHERE key = ?", (inbound_id, key)
        )
        await db.commit()


async def deactivate_server(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE servers SET is_active = 0 WHERE key = ?", (key,)
        )
        await db.commit()


async def server_exists(key: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM servers WHERE key = ? AND is_active = 1", (key,)
        ) as cursor:
            return await cursor.fetchone() is not None


async def get_setting(key: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()


async def get_all_settings() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT key, value FROM settings") as cursor:
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}
