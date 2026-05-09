import asyncio
import logging
import time
from datetime import date, datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)

import database
from config import ADMIN_ID
from xui_client import XUIClient
from handlers.start import admin_keyboard

logger = logging.getLogger(__name__)
router = Router()

GB = 1024 ** 3


class StatsState(StatesGroup):
    SelectServer = State()
    ServerMenu = State()
    FindUser = State()


def _server_select_kb(servers: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🧪 Тест серверов", callback_data="stats:test")]
    ]
    buttons += [
        [InlineKeyboardButton(text=s["button_name"], callback_data=f"stats:srv:{s['key']}")]
        for s in servers
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="stats:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _server_menu_kb(server_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Все пользователи", callback_data=f"stats:all:{server_key}"),
            InlineKeyboardButton(text="🖥 Статус", callback_data=f"stats:status:{server_key}"),
        ],
        [InlineKeyboardButton(text="➕ Новый пользователь", callback_data=f"stats:new:{server_key}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="stats:back")],
    ])


def _fmt_bytes(b: int) -> str:
    if b >= GB:
        return f"{b / GB:.1f} GB"
    if b >= 1024 ** 2:
        return f"{b / 1024**2:.1f} MB"
    return f"{b} B"


def _fmt_used(b: int) -> str:
    return f"{b / 1024**2:.0f} MB"


def _client_status(client: dict, stats: dict, online: bool = False) -> str:
    now_ms = int(time.time() * 1000)
    expiry = client.get("expiryTime", 0)
    total = client.get("totalGB", 0)
    used_up = stats.get("up", 0) + stats.get("down", 0) if stats else 0

    expired = expiry > 0 and expiry < now_ms
    expiring_soon = expiry > 0 and (expiry - now_ms) < 7 * 24 * 3600 * 1000
    traffic_pct = (used_up / total * 100) if total > 0 else 0
    traffic_warn = total > 0 and traffic_pct >= 90

    if expired:
        return "🔴"
    if expiring_soon or traffic_warn:
        return "🟡"
    if online:
        return "✅"
    return "🟢"


def _fmt_expiry(expiry_ms: int) -> str:
    if expiry_ms == 0:
        return "Бессрочно"
    d = datetime.fromtimestamp(expiry_ms / 1000).date()
    days = (d - date.today()).days
    sign = "+" if days >= 0 else ""
    return f"{d.strftime('%d.%m.%Y')} ({sign}{days} дн.)"


# ─── Entry ────────────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Стат")
async def stats_entry(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    servers = await database.get_all_servers()
    if not servers:
        await message.answer("Серверы не добавлены.")
        return
    await state.set_state(StatsState.SelectServer)
    await state.update_data(servers=servers)
    await message.answer("Выбери сервер:", reply_markup=_server_select_kb(servers))


@router.callback_query(F.data == "stats:cancel")
async def stats_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Отменено.", reply_markup=admin_keyboard())
    await call.answer()


@router.callback_query(F.data == "stats:back")
async def stats_back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    servers = data.get("servers", [])
    await state.set_state(StatsState.SelectServer)
    await call.message.edit_text("Выбери сервер:", reply_markup=_server_select_kb(servers))
    await call.answer()


@router.callback_query(F.data.startswith("stats:srv:"))
async def stats_server_selected(call: CallbackQuery, state: FSMContext):
    server_key = call.data.split(":", 2)[2]
    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return
    await state.update_data(current_server=server)
    await state.set_state(StatsState.ServerMenu)
    await call.message.edit_text(
        f"🖥 {server['button_name']}",
        reply_markup=_server_menu_kb(server_key),
    )
    await call.answer()


# ─── Test All Servers ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "stats:test")
async def stats_test(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    servers = data.get("servers") or await database.get_all_servers()

    await call.message.edit_text("⏳ Проверяю все серверы...")

    async def check_server(server: dict):
        xui = XUIClient(server["url"], server["username"], server["password"])
        t0 = time.monotonic()
        try:
            if not await xui.login():
                return server, None, None, None
            ping_ms = int((time.monotonic() - t0) * 1000)
            clients = await xui.get_all_clients(server["inbound_id"])
            online = await xui.get_online_clients()
            return server, len(clients), len(online or []), ping_ms
        except Exception as e:
            logger.error(f"test check_server {server['key']}: {e}")
            return server, None, None, None
        finally:
            await xui.logout()

    results = await asyncio.gather(*[check_server(s) for s in servers])

    now_str = datetime.now().strftime("%d.%m.%y %H:%M")
    lines = [f"🧪 <b>Тест серверов</b> · {now_str}\n"]

    total_clients = 0
    total_online = 0
    ok_count = 0
    dead_keys = []

    for server, clients, online, ping_ms in results:
        name = server["button_name"]
        if clients is None:
            dead_keys.append(server["key"])
            lines.append(f"🔴 {name} · недоступен")
        else:
            ok_count += 1
            total_clients += clients
            total_online += online
            lines.append(f"🟢 {name} · {clients} польз. · онлайн: {online} · {ping_ms}ms")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━")
    lines.append(f"Серверов онлайн: {ok_count}/{len(servers)}")
    lines.append(f"Всего подключений: {total_clients}")
    lines.append(f"Онлайн сейчас: {total_online}")

    text = "\n".join(lines)
    kb_rows = []
    if dead_keys:
        dead_str = ",".join(dead_keys)
        kb_rows.append([InlineKeyboardButton(
            text=f"🔄 Перезапустить упавшие ({len(dead_keys)})",
            callback_data=f"stats:restart_dead:{dead_str}"
        )])
    kb_rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="stats:back")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")


# ─── Restart Dead Servers ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("stats:restart_dead:"))
async def stats_restart_dead(call: CallbackQuery, state: FSMContext):
    await call.answer()
    dead_keys = call.data.split(":", 2)[2].split(",")
    await call.message.edit_text(f"🔄 Перезапускаю Xray на {len(dead_keys)} серверах...")

    async def restart_one(server: dict):
        xui = XUIClient(server["url"], server["username"], server["password"])
        try:
            if not await xui.login():
                return server["button_name"], False
            ok = await xui.restart_xray()
            return server["button_name"], ok
        except Exception as e:
            logger.error(f"restart_dead {server['key']}: {e}")
            return server["button_name"], False
        finally:
            await xui.logout()

    servers = [await database.get_server(k) for k in dead_keys]
    servers = [s for s in servers if s]
    results = await asyncio.gather(*[restart_one(s) for s in servers])

    lines = ["🔄 <b>Результат перезапуска</b>\n"]
    for name, ok in results:
        lines.append(f"{'✅' if ok else '❌'} {name}")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Повторить тест", callback_data="stats:test")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="stats:back")],
    ])
    await call.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")


# ─── All Users ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("stats:all:"))
async def stats_all_users(call: CallbackQuery, state: FSMContext):
    server_key = call.data.split(":", 2)[2]
    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return

    await call.message.edit_text("⏳ Загружаю список пользователей...")
    await call.answer()

    client = XUIClient(server["url"], server["username"], server["password"])
    try:
        if not await client.login():
            await call.message.edit_text("❌ Не удалось подключиться к серверу.")
            return

        inbounds = await client.get_inbounds_list()
        online_list = await client.get_online_clients()
        online_set = set(online_list or [])

        # Собираем всех клиентов со всех инбаундов
        import json as _json
        all_clients = []
        for ib in inbounds:
            ib_id = ib.get("id")
            ib_remark = ib.get("remark", "")
            settings = ib.get("settings", "{}")
            if isinstance(settings, str):
                try: settings = _json.loads(settings)
                except: settings = {}
            for c in settings.get("clients", []):
                all_clients.append((c, ib_id, ib_remark))

        if not all_clients:
            await call.message.edit_text(
                "Пользователей нет.",
                reply_markup=_server_menu_kb(server_key),
            )
            return

        buttons = []
        row = []
        for c, ib_id, ib_remark in all_clients:
            email = c.get("email", "?")
            now_ms = int(time.time() * 1000)
            expiry = c.get("expiryTime", 0)
            if expiry > 0 and expiry < now_ms:
                status = "🔴"
            elif expiry > 0 and (expiry - now_ms) < 7 * 24 * 3600 * 1000:
                status = "🟡"
            elif email in online_set:
                status = "✅"
            else:
                status = "🟢"
            btn = InlineKeyboardButton(
                text=f"{status} {email}",
                callback_data=f"stats:card:{server_key}:{ib_id}:{email}"
            )
            row.append(btn)
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="stats:back")])

        await call.message.edit_text(
            f"📋 {server['button_name']} — {len(all_clients)} польз.:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
    finally:
        await client.logout()


# ─── User Card ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("stats:card:"))
async def stats_user_card(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":", 4)
    server_key = parts[2]
    inbound_id = int(parts[3])
    email = parts[4]

    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return

    await call.answer()
    xui = XUIClient(server["url"], server["username"], server["password"])
    try:
        if not await xui.login():
            await call.message.answer("❌ Не удалось подключиться к серверу.")
            return

        import json as _json
        inbound = await xui.get_inbound_info(inbound_id)
        if not inbound:
            await call.message.answer("❌ Инбаунд не найден.")
            return
        settings = inbound.get("settings", "{}")
        if isinstance(settings, str):
            try: settings = _json.loads(settings)
            except: settings = {}
        c = next((x for x in settings.get("clients", []) if x.get("email") == email), None)
        if not c:
            await call.message.answer("❌ Пользователь не найден.")
            return

        stats_data = await xui.get_client_stats(email)
        online_list = await xui.get_online_clients()
        online = email in set(online_list or [])
        status = _client_status(c, stats_data, online=online)

        used = (stats_data.get("up", 0) + stats_data.get("down", 0)) if stats_data else 0
        used_str = _fmt_used(used)

        expiry_ms = c.get("expiryTime", 0)
        if expiry_ms:
            expiry_date = datetime.fromtimestamp(expiry_ms / 1000).date()
            days_left = (expiry_date - date.today()).days
            if days_left > 300:
                expiry_line = f"📅 {expiry_date.strftime('%m.%y')}"
            else:
                expiry_line = f"📅 {expiry_date.strftime('%m.%y')} · {days_left} дн."
        else:
            expiry_line = "📅 Бессрочно"

        client_id = c.get("id", "")
        text = f"{status} {email}\n📦 {used_str}\n{expiry_line}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 RELAY WL",
                    callback_data=f"stats:sublink:{server_key}:{inbound_id}:{email}"
                ),
                InlineKeyboardButton(
                    text="🔗 RELAY RU",
                    callback_data=f"stats:router:{client_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="ПРОДЛИТЬ",
                    callback_data=f"stats:extend:{server_key}:{inbound_id}:{email}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"stats:delask:{server_key}:{inbound_id}:{email}"
                ),
            ],
        ])
        await call.message.answer(text, reply_markup=kb)
    finally:
        await xui.logout()


# ─── Delete User ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("stats:delask:"))
async def stats_del_ask(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":", 4)
    server_key = parts[2]
    inbound_id = parts[3]
    email = parts[4]
    await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Да, удалить",
                callback_data=f"stats:deldo:{server_key}:{inbound_id}:{email}"
            ),
            InlineKeyboardButton(text="❌ Отмена", callback_data="stats:delcancel"),
        ]
    ])
    await call.message.answer(f"Удалить пользователя {email}?", reply_markup=kb)


@router.callback_query(F.data == "stats:delcancel")
async def stats_del_cancel(call: CallbackQuery, state: FSMContext):
    await call.answer("Отменено.")
    await call.message.delete()


@router.callback_query(F.data.startswith("stats:deldo:"))
async def stats_del_do(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":", 4)
    server_key = parts[2]
    inbound_id = int(parts[3])
    email = parts[4]

    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return

    await call.answer("⏳ Удаляю...")
    xui = XUIClient(server["url"], server["username"], server["password"])
    try:
        if not await xui.login():
            await call.message.edit_text("❌ Не удалось подключиться к серверу.")
            return

        import json as _json
        inbound = await xui.get_inbound_info(inbound_id)
        if not inbound:
            await call.message.edit_text("❌ Инбаунд не найден.")
            return
        settings = inbound.get("settings", "{}")
        if isinstance(settings, str):
            try: settings = _json.loads(settings)
            except: settings = {}
        c = next((x for x in settings.get("clients", []) if x.get("email") == email), None)
        if not c:
            await call.message.edit_text("❌ Пользователь не найден.")
            return

        client_uuid = c.get("id", "")
        ok = await xui.delete_client(inbound_id, client_uuid)
        if ok:
            await call.message.edit_text(f"✅ Пользователь {email} удалён.")
        else:
            await call.message.edit_text(f"❌ Не удалось удалить {email}.")
    finally:
        await xui.logout()


# ─── Extend User (+1 year) ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("stats:extend:"))
async def stats_extend(call: CallbackQuery, state: FSMContext):
    import json as _json
    parts = call.data.split(":", 4)
    server_key = parts[2]
    inbound_id = int(parts[3])
    email = parts[4]

    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return

    await call.answer("⏳ Продлеваю...")
    xui = XUIClient(server["url"], server["username"], server["password"])
    try:
        if not await xui.login():
            await call.message.answer("❌ Не удалось подключиться к серверу.")
            return

        inbound = await xui.get_inbound_info(inbound_id)
        if not inbound:
            await call.message.answer("❌ Инбаунд не найден.")
            return
        settings = inbound.get("settings", "{}")
        if isinstance(settings, str):
            try: settings = _json.loads(settings)
            except: settings = {}
        c = next((x for x in settings.get("clients", []) if x.get("email") == email), None)
        if not c:
            await call.message.answer("❌ Клиент не найден.")
            return

        client_uuid = c.get("id", "")
        current_expiry_ms = c.get("expiryTime", 0)
        today = date.today()
        if current_expiry_ms and current_expiry_ms > 0:
            current_date = datetime.fromtimestamp(current_expiry_ms / 1000).date()
            base = current_date if current_date > today else today
        else:
            base = today
        new_date = date(base.year + 1, base.month, base.day)
        new_expiry_ms = int(datetime(new_date.year, new_date.month, new_date.day, 23, 59, 59).timestamp() * 1000)

        ok = await xui.update_client_expiry(inbound_id, client_uuid, c, new_expiry_ms)
        if ok:
            await call.message.answer(f"✅ {email} продлён до {new_date.strftime('%d.%m.%Y')}")
        else:
            await call.message.answer(f"❌ Не удалось продлить {email}.")
    finally:
        await xui.logout()


# ─── Subscription Link (RELAY WL) ────────────────────────────────────────────

@router.callback_query(F.data.startswith("stats:sublink:"))
async def stats_sub_link(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":", 4)
    server_key = parts[2]
    inbound_id = int(parts[3])
    email = parts[4]

    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return

    await call.answer("⏳")
    xui = XUIClient(server["url"], server["username"], server["password"])
    try:
        if not await xui.login():
            await call.message.answer("❌ Не удалось подключиться.")
            return
        import json as _json
        inbound = await xui.get_inbound_info(inbound_id)
        if not inbound:
            await call.message.answer("❌ Инбаунд не найден.")
            return
        settings = inbound.get("settings", "{}")
        if isinstance(settings, str):
            try: settings = _json.loads(settings)
            except: settings = {}
        c = next((x for x in settings.get("clients", []) if x.get("email") == email), None)
        if not c:
            await call.message.answer("❌ Клиент не найден.")
            return
        uuid = c.get("id", "")
        sub_url = f"https://white.theredhat.su:8888/sub/{uuid}"
        await call.message.answer(f"<pre>{sub_url}</pre>", parse_mode="HTML")
    finally:
        await xui.logout()


# ─── Router Link ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("stats:router:"))
async def stats_router_link(call: CallbackQuery, state: FSMContext):
    import aiohttp, base64
    client_uuid = call.data.split(":", 2)[2]
    await call.answer("⏳ Генерирую ссылку для роутера...")

    sub_url = f"https://white.theredhat.su:8888/sub/{client_uuid}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(sub_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    await call.message.answer(f"❌ Сервер подписок вернул {resp.status}")
                    return
                raw = await resp.read()
        decoded = base64.b64decode(raw).decode("utf-8").strip()
        links = [l for l in decoded.splitlines() if l.startswith("vless://")]
        if not links:
            await call.message.answer("❌ Ссылки не найдены в подписке.")
            return
        text = "\n\n".join(f"<pre>{l}</pre>" for l in links)
        await call.message.answer(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"stats_router_link error: {e}")
        await call.message.answer(f"❌ Ошибка: {e}")


# ─── Find User ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("stats:new:"))
async def stats_new_user(call: CallbackQuery, state: FSMContext):
    from handlers.create_user import CreateUser, _server_kb
    server_key = call.data.split(":", 2)[2]
    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return
    servers = await database.get_all_servers()
    await state.set_state(CreateUser.SelectServer)
    await state.update_data(servers=servers)
    await call.message.answer("Выбери сервер:", reply_markup=_server_kb(servers))
    await call.answer()


# ─── Get Link ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("stats:link:"))
async def stats_get_link(call: CallbackQuery, state: FSMContext):
    from link_builder import build_link
    parts = call.data.split(":", 4)
    # stats:link:{server_key}:{inbound_id}:{email}
    server_key = parts[2]
    inbound_id = int(parts[3])
    email = parts[4]

    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return

    await call.answer("⏳ Генерирую ссылку...")
    xui = XUIClient(server["url"], server["username"], server["password"])
    try:
        if not await xui.login():
            await call.message.answer("❌ Не удалось подключиться к серверу.")
            return

        inbound = await xui.get_inbound_info(inbound_id)
        if not inbound:
            await call.message.answer("❌ Не удалось получить данные inbound.")
            return

        # Найти UUID клиента по email
        import json as _json
        settings = inbound.get("settings", "{}")
        if isinstance(settings, str):
            settings = _json.loads(settings)
        clients = settings.get("clients", [])
        client_uuid = ""
        client_password = ""
        for c in clients:
            if c.get("email") == email:
                client_uuid = c.get("id", "")
                client_password = c.get("password", "")
                break

        if not client_uuid:
            await call.message.answer("❌ Клиент не найден.")
            return

        db_settings = await database.get_all_settings()
        prefix = db_settings.get("profile_prefix", "")
        postfix = db_settings.get("profile_postfix", "")
        flag = server["country_flag"]
        profile_name = f"{prefix}{email}{postfix}{flag}"

        link = build_link(inbound, client_uuid, client_password, profile_name, server["url"])

        await call.message.answer(f"<pre>{link}</pre>", parse_mode="HTML")
    finally:
        await xui.logout()


@router.message(StatsState.FindUser)
async def find_user_search(message: Message, state: FSMContext):
    nick = message.text.strip().lower().replace(" ", "_")
    servers = await database.get_all_servers()

    await message.answer(f"🔍 Ищу {nick} на всех серверах...")

    async def search_server(server: dict):
        client = XUIClient(server["url"], server["username"], server["password"])
        try:
            if not await client.login():
                return None
            clients = await client.get_all_clients(server["inbound_id"])
            for c in clients:
                if c.get("email", "").lower() == nick:
                    stats = await client.get_client_stats(c["email"])
                    return server, c, stats
            return None
        except Exception as e:
            logger.error(f"search_server error: {e}")
            return None
        finally:
            await client.logout()

    results = await asyncio.gather(*[search_server(s) for s in servers])
    found = [r for r in results if r]

    if not found:
        await message.answer(f"Пользователь '{nick}' не найден ни на одном сервере.")
        return

    for server, c, stats in found:
        email = c.get("email", "?")
        total_bytes = c.get("totalGB", 0)
        used = (stats.get("up", 0) + stats.get("down", 0)) if stats else 0
        remaining = max(total_bytes - used, 0) if total_bytes else 0
        expiry_str = _fmt_expiry(c.get("expiryTime", 0))
        status = _client_status(c, stats)
        note = c.get("comment", "—")
        traffic_str = (
            f"{_fmt_bytes(used)} / {_fmt_bytes(total_bytes)}"
            if total_bytes else f"{_fmt_bytes(used)} / ♾"
        )
        remaining_str = _fmt_bytes(remaining) if total_bytes else "—"

        text = (
            f"👤 {email}\n"
            f"Сервер:       {server['button_name']}\n"
            f"Использовано: {traffic_str}\n"
            f"Осталось:     {remaining_str}\n"
            f"До:           {expiry_str}\n"
            f"Примечание:   {note}\n"
            f"Статус:       {status}"
        )
        await message.answer(text)

    data = await state.get_data()
    server_key = data.get("find_server_key", "")
    await state.set_state(StatsState.ServerMenu)


# ─── Server Status ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("stats:status:"))
async def stats_server_status(call: CallbackQuery, state: FSMContext):
    server_key = call.data.split(":", 2)[2]
    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return

    await call.message.edit_text("⏳ Получаю статус сервера...")
    await call.answer()

    client = XUIClient(server["url"], server["username"], server["password"])
    t0 = time.monotonic()
    try:
        if not await client.login():
            await call.message.edit_text(
                f"🖥 {server['button_name']}\nПанель: 🔴 Недоступна",
                reply_markup=_server_menu_kb(server_key),
            )
            return
        ping_ms = int((time.monotonic() - t0) * 1000)

        status = await client.get_server_status()
        if not status:
            await call.message.edit_text(
                f"🖥 {server['button_name']}\nПанель: 🟢 Онлайн\nПинг: {ping_ms}ms\nСтатус Xray: недоступен",
                reply_markup=_server_menu_kb(server_key),
            )
            return

        xray = status.get("xray", {})
        xray_running = xray.get("state", "") == "Running"
        xray_status = "🟢 Запущен" if xray_running else "🔴 Остановлен"
        xray_version = xray.get("version", "?")

        uptime_sec = status.get("uptime", 0)
        uptime_days = uptime_sec // 86400
        uptime_hours = (uptime_sec % 86400) // 3600
        uptime_str = f"{uptime_days} дней {uptime_hours} часов"

        cpu = status.get("cpu", 0)
        mem = status.get("mem", {})
        mem_cur = mem.get("current", 0)
        mem_total = mem.get("total", 0)
        mem_str = f"{mem_cur / GB:.1f} GB / {mem_total / GB:.1f} GB"

        text = (
            f"🖥 {server['button_name']}\n"
            f"Панель:  🟢 Онлайн\n"
            f"Xray:    {xray_status}\n"
            f"Uptime:  {uptime_str}\n"
            f"Версия:  Xray {xray_version}\n"
            f"CPU:     {cpu:.0f}%\n"
            f"RAM:     {mem_str}\n"
            f"Пинг:    {ping_ms}ms"
        )
        await call.message.edit_text(text, reply_markup=_server_menu_kb(server_key))
    finally:
        await client.logout()
