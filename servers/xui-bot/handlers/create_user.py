import logging
from datetime import date, timedelta
from urllib.parse import quote

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    LinkPreviewOptions,
)

import aiohttp

import database
from config import ADMIN_ID
from xui_client import XUIClient
from link_builder import build_link
from calendar_widget import create_calendar, create_quick_buttons, process_calendar_selection
from handlers.start import admin_keyboard

logger = logging.getLogger(__name__)
router = Router()

GB = 1024 ** 3


class CreateUser(StatesGroup):
    SelectServer = State()
    SelectInbound = State()
    EnterNick = State()
    EnterNote = State()
    SelectTraffic = State()
    SelectExpiry = State()
    EnterCustomDate = State()
    Confirm = State()


class EditField(StatesGroup):
    Nick = State()
    Note = State()
    Traffic = State()
    Expiry = State()
    CustomDate = State()


async def _get_happ_link(sub_url: str) -> str | None:
    """Получает encrypted deep link happ://crypt5/... через API crypto.happ.su."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://crypto.happ.su/api-v2.php",
                json={"url": sub_url},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return data.get("url") or data.get("link")
    except Exception as e:
        logger.warning("crypto.happ.su failed: %s", e)
    return None


def _happ_redirect_url(uuid: str, name: str = "VPN") -> str:
    return f"http://82.38.66.75:8090/r/happ/{uuid}?name={quote(name)}"


def _back_kb(*extra_buttons):
    buttons = [[KeyboardButton(text="🔙 Назад")]]
    for row in extra_buttons:
        buttons.append(row)
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# Три инбаунда для bundle: CZ3-2082, PL4-2052, Fin-2525
BUNDLE_INBOUNDS = [
    {"server_key": "ApeCZ3",   "inbound_id": 15, "display": "🇨🇿 CZ3-2082", "short": "CZ3"},
    {"server_key": "POLAND_4", "inbound_id": 8,  "display": "🇵🇱 PL4-2052", "short": "PL4"},
    {"server_key": "hostfin",  "inbound_id": 5,  "display": "🇫🇮 Fin-2525", "short": "Fin"},
    {"server_key": "italy_red", "inbound_id": 1,  "display": "🇮🇹 Italy-2083", "short": "Italy"},
]
BUNDLE_LABEL = "🌐 4 сервера\nCZ3 · PL4 · Fin · Italy"
CZ4_KEY = "maryart_cz4"


def _server_kb(servers: list[dict]) -> ReplyKeyboardMarkup:
    cz4 = next((s for s in servers if s["key"] == CZ4_KEY), None)
    cz4_row = [[KeyboardButton(text=cz4["button_name"])]] if cz4 else []
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUNDLE_LABEL)],
            *cz4_row,
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


def _inbound_kb(inbounds: list) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=inb.get("remark") or str(inb["id"]))] for inb in inbounds]
    rows.append([KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _traffic_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1 GB"), KeyboardButton(text="100 GB")],
            [KeyboardButton(text="300 GB"), KeyboardButton(text="500 GB")],
            [KeyboardButton(text="1000 GB")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def _expiry_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="3 дня"), KeyboardButton(text="7 дней")],
            [KeyboardButton(text="+ 1 год")],
            [KeyboardButton(text="📅 Выбрать дату")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def _confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Выполнить", callback_data="cu:confirm"),
            InlineKeyboardButton(text="❌ Отмена",   callback_data="cu:cancel"),
        ],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="cu:edit")],
    ])


def _edit_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Ник",          callback_data="cu:ed:nick"),
            InlineKeyboardButton(text="📝 Примечание",   callback_data="cu:ed:note"),
        ],
        [
            InlineKeyboardButton(text="📦 Трафик",       callback_data="cu:ed:traffic"),
            InlineKeyboardButton(text="📅 Срок",         callback_data="cu:ed:expiry"),
        ],
        [InlineKeyboardButton(text="↩️ Назад",           callback_data="cu:ed:back")],
    ])


def _add_months(d: date, months: int) -> date:
    import calendar
    month = d.month + months
    year = d.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _to_date(d) -> date:
    return date.fromisoformat(d) if isinstance(d, str) else d


def _days_until(d) -> int:
    return (_to_date(d) - date.today()).days


def _traffic_label(traffic_gb: int) -> str:
    return "♾ Безлимит" if traffic_gb == 0 else f"{traffic_gb} GB"


async def _show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    nick = data["nick"]
    note = data.get("note", "—")
    traffic_gb = data["traffic_gb"]
    expiry_date = _to_date(data["expiry_date"])
    days = _days_until(expiry_date)

    if data.get("bundle_mode"):
        bundle = data["bundle"]
        servers_line = " + ".join(b["display"] for b in bundle)
        text = (
            "📋 Проверь данные:\n\n"
            f"Серверы:     {servers_line}\n"
            f"Ник:         {nick}\n"
            f"Примечание:  {note}\n"
            f"Трафик:      {_traffic_label(traffic_gb)}\n"
            f"До:          {expiry_date.strftime('%d.%m.%Y')} ({days} дней)\n"
        )
    else:
        server = data["server"]
        inbound_remark = data.get("inbound_remark")
        flag = server["country_flag"]
        server_suffix = f"_{server['key']}{flag}"
        profile_name = f"{nick}{server_suffix}"
        inbound_line = f"Инбаунд:     {inbound_remark}\n" if inbound_remark else ""
        text = (
            "📋 Проверь данные:\n\n"
            f"Сервер:      {server['button_name']}\n"
            f"{inbound_line}"
            f"Ник:         {nick}\n"
            f"Примечание:  {note}\n"
            f"Трафик:      {_traffic_label(traffic_gb)}\n"
            f"До:          {expiry_date.strftime('%d.%m.%Y')} ({days} дней)\n"
            f"Профиль:     {profile_name}\n"
        )
    await message.answer(text, reply_markup=_confirm_kb())
    await state.set_state(CreateUser.Confirm)


async def _go_select_inbound(message: Message, state: FSMContext, server: dict, servers: list):
    """Получает инбаунды сервера. Если один — выбирает автоматически, если несколько — показывает список."""
    wait_msg = await message.answer("⏳ Получаю список инбаундов...")
    client = XUIClient(server["url"], server["username"], server["password"])
    try:
        if not await client.login():
            await wait_msg.delete()
            await message.answer("❌ Не удалось подключиться к серверу.")
            return
        inbounds = await client.get_inbounds_list()
    finally:
        await client.logout()

    await wait_msg.delete()

    if not inbounds:
        # Нет инбаундов — используем дефолтный из сервера
        await state.update_data(
            server=server, servers=servers,
            inbounds=[], selected_inbound_id=server["inbound_id"], inbound_remark=None
        )
        await state.set_state(CreateUser.EnterNick)
        await message.answer(
            f"Сервер: {server['button_name']}\nВведи ник пользователя:",
            reply_markup=_back_kb(),
        )
        return

    if len(inbounds) == 1:
        inb = inbounds[0]
        remark = inb.get("remark") or str(inb["id"])
        await state.update_data(
            server=server, servers=servers,
            inbounds=inbounds, selected_inbound_id=inb["id"], inbound_remark=remark
        )
        await state.set_state(CreateUser.EnterNick)
        await message.answer(
            f"Сервер: {server['button_name']}\nВведи ник пользователя:",
            reply_markup=_back_kb(),
        )
        return

    # Несколько инбаундов — показываем выбор
    await state.update_data(
        server=server, servers=servers,
        inbounds=inbounds, selected_inbound_id=None, inbound_remark=None
    )
    await state.set_state(CreateUser.SelectInbound)
    await message.answer("Выбери инбаунд:", reply_markup=_inbound_kb(inbounds))


# ─── Entry ────────────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Новый")
async def start_create(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    servers = await database.get_all_servers()
    if not servers:
        await message.answer("Серверы не добавлены. Сначала добавьте сервер.")
        return

    await state.set_state(CreateUser.SelectServer)
    await state.update_data(servers=servers)
    await message.answer("Выбери сервер:", reply_markup=_server_kb(servers))


# ─── Step 1: Select Server ────────────────────────────────────────────────────

@router.message(CreateUser.SelectServer)
async def select_server(message: Message, state: FSMContext):
    data = await state.get_data()
    servers = data.get("servers", [])

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=admin_keyboard())
        return

    if message.text == BUNDLE_LABEL:
        # Собираем данные bundle-серверов из БД
        bundle = []
        for bi in BUNDLE_INBOUNDS:
            srv = next((s for s in servers if s["key"] == bi["server_key"]), None)
            if srv:
                bundle.append({**bi, "url": srv["url"], "username": srv["username"], "password": srv["password"]})
        if not bundle:
            await message.answer("❌ Не найдены серверы для bundle в БД.")
            return
        await state.update_data(bundle_mode=True, bundle=bundle, server=None)
        await state.set_state(CreateUser.EnterNick)
        await message.answer("Введи ник пользователя:", reply_markup=_back_kb())
        return

    server = next((s for s in servers if s["button_name"] == message.text), None)
    if not server:
        await message.answer("Выбери сервер из списка.")
        return

    await _go_select_inbound(message, state, server, servers)


# ─── Step 2: Select Inbound ───────────────────────────────────────────────────

@router.message(CreateUser.SelectInbound, F.text == "🔙 Назад")
async def inbound_back(message: Message, state: FSMContext):
    data = await state.get_data()
    servers = data.get("servers", [])
    await state.set_state(CreateUser.SelectServer)
    await state.update_data(server=None, selected_inbound_id=None, inbound_remark=None)
    await message.answer("Выбери сервер:", reply_markup=_server_kb(servers))


@router.message(CreateUser.SelectInbound)
async def select_inbound(message: Message, state: FSMContext):
    data = await state.get_data()
    inbounds = data.get("inbounds", [])
    inbound = next(
        (inb for inb in inbounds if (inb.get("remark") or str(inb["id"])) == message.text),
        None
    )
    if not inbound:
        await message.answer("Выбери инбаунд из списка.")
        return
    remark = inbound.get("remark") or str(inbound["id"])
    await state.update_data(selected_inbound_id=inbound["id"], inbound_remark=remark)
    await state.set_state(CreateUser.EnterNick)
    await message.answer("Введи ник пользователя:", reply_markup=_back_kb())


# ─── Step 3: Enter Nick ───────────────────────────────────────────────────────

@router.message(CreateUser.EnterNick, F.text == "🔙 Назад")
async def nick_back(message: Message, state: FSMContext):
    data = await state.get_data()
    inbounds = data.get("inbounds", [])
    servers = data.get("servers", [])
    if len(inbounds) > 1:
        await state.set_state(CreateUser.SelectInbound)
        await state.update_data(selected_inbound_id=None, inbound_remark=None)
        await message.answer("Выбери инбаунд:", reply_markup=_inbound_kb(inbounds))
    else:
        await state.set_state(CreateUser.SelectServer)
        await state.update_data(server=None)
        await message.answer("Выбери сервер:", reply_markup=_server_kb(servers))


@router.message(CreateUser.EnterNick)
async def enter_nick(message: Message, state: FSMContext):
    nick = message.text.strip()
    if not nick:
        await message.answer("Ник не может быть пустым.")
        return
    await state.update_data(nick=nick)
    await state.set_state(CreateUser.EnterNote)
    await message.answer(
        "Введи примечание (или пропусти):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="➡️ Пропустить")]
            ],
            resize_keyboard=True,
        ),
    )


# ─── Step 4: Enter Note ───────────────────────────────────────────────────────

@router.message(CreateUser.EnterNote, F.text == "🔙 Назад")
async def note_back(message: Message, state: FSMContext):
    await state.set_state(CreateUser.EnterNick)
    await message.answer("Введи ник пользователя:", reply_markup=_back_kb())


@router.message(CreateUser.EnterNote)
async def enter_note(message: Message, state: FSMContext):
    note = "" if message.text == "➡️ Пропустить" else message.text.strip()
    await state.update_data(note=note)
    await state.set_state(CreateUser.SelectTraffic)
    await message.answer("Выбери лимит трафика:", reply_markup=_traffic_kb())


# ─── Step 5: Select Traffic ───────────────────────────────────────────────────

TRAFFIC_MAP = {
    "1 GB": 1, "100 GB": 100, "300 GB": 300, "500 GB": 500, "1000 GB": 1000,
}


@router.message(CreateUser.SelectTraffic, F.text == "🔙 Назад")
async def traffic_back(message: Message, state: FSMContext):
    await state.set_state(CreateUser.EnterNote)
    await message.answer(
        "Введи примечание (или пропусти):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Назад"), KeyboardButton(text="➡️ Пропустить")]],
            resize_keyboard=True,
        ),
    )


@router.message(CreateUser.SelectTraffic)
async def select_traffic(message: Message, state: FSMContext):
    gb = TRAFFIC_MAP.get(message.text)
    if gb is None:
        await message.answer("Выбери трафик из кнопок.")
        return
    await state.update_data(traffic_gb=gb)
    await state.set_state(CreateUser.SelectExpiry)
    await message.answer("Выбери срок действия:", reply_markup=_expiry_kb())


# ─── Step 6: Select Expiry ────────────────────────────────────────────────────

@router.message(CreateUser.SelectExpiry, F.text == "🔙 Назад")
async def expiry_back(message: Message, state: FSMContext):
    await state.set_state(CreateUser.SelectTraffic)
    await message.answer("Выбери лимит трафика:", reply_markup=_traffic_kb())


@router.message(CreateUser.SelectExpiry, F.text == "📅 Выбрать дату")
async def expiry_custom(message: Message, state: FSMContext):
    await state.set_state(CreateUser.EnterCustomDate)
    today = date.today()
    kb = create_calendar(today.year, today.month)
    quick = create_quick_buttons()
    await message.answer("Выбери дату:", reply_markup=quick)
    await message.answer("📅", reply_markup=kb)


@router.message(CreateUser.SelectExpiry)
async def select_expiry(message: Message, state: FSMContext):
    today = date.today()
    mapping = {
        "3 дня": today + timedelta(days=3),
        "7 дней": today + timedelta(days=7),
        "+ 1 год": date(today.year + 1, today.month, today.day),
    }
    expiry = mapping.get(message.text)
    if not expiry:
        await message.answer("Выбери срок из кнопок.")
        return
    await state.update_data(expiry_date=expiry)
    await _show_confirm(message, state)


# ─── Step 6b: Calendar ────────────────────────────────────────────────────────

@router.callback_query(CreateUser.EnterCustomDate, F.data.startswith("cal:"))
async def calendar_cb(call: CallbackQuery, state: FSMContext):
    data = call.data
    parts = data.split(":")
    action = parts[1]

    if action in ("prev", "next"):
        year, month = int(parts[2]), int(parts[3])
        kb = create_calendar(year, month)
        await call.message.edit_reply_markup(reply_markup=kb)
        await call.answer()
        return

    if action == "cancel":
        await call.answer()
        await state.set_state(CreateUser.SelectExpiry)
        await call.message.answer("Выбери срок действия:", reply_markup=_expiry_kb())
        return

    if action == "ignore":
        await call.answer()
        return

    selected = process_calendar_selection(data)
    if selected:
        await state.update_data(expiry_date=selected)
        await call.message.delete()
        await _show_confirm(call.message, state)
    else:
        await call.answer("Выбери дату начиная с завтра.", show_alert=True)


# ─── Edit from Confirm ────────────────────────────────────────────────────────

@router.callback_query(CreateUser.Confirm, F.data == "cu:edit")
async def confirm_edit_menu(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=_edit_menu_kb())
    await call.answer()


@router.callback_query(F.data == "cu:ed:back")
async def edit_back_to_confirm(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateUser.Confirm)
    await call.message.edit_reply_markup(reply_markup=_confirm_kb())
    await call.answer()


@router.callback_query(F.data == "cu:ed:nick")
async def edit_nick_start(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(EditField.Nick)
    await call.message.answer(f"Введи новый ник (сейчас: {data.get('nick', '')}):",
                              reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
    await call.answer()


@router.message(EditField.Nick)
async def edit_nick_done(message: Message, state: FSMContext):
    nick = message.text.strip()
    if not nick:
        await message.answer("Ник не может быть пустым.")
        return
    await state.update_data(nick=nick)
    await state.set_state(CreateUser.Confirm)
    await _show_confirm(message, state)


@router.callback_query(F.data == "cu:ed:note")
async def edit_note_start(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current = data.get("note") or "—"
    await state.set_state(EditField.Note)
    await call.message.answer(
        f"Введи новое примечание (сейчас: {current}):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="➡️ Пропустить")]],
            resize_keyboard=True,
        ),
    )
    await call.answer()


@router.message(EditField.Note)
async def edit_note_done(message: Message, state: FSMContext):
    note = "" if message.text == "➡️ Пропустить" else message.text.strip()
    await state.update_data(note=note)
    await state.set_state(CreateUser.Confirm)
    await _show_confirm(message, state)


@router.callback_query(F.data == "cu:ed:traffic")
async def edit_traffic_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditField.Traffic)
    await call.message.answer("Выбери новый лимит трафика:", reply_markup=_traffic_kb())
    await call.answer()


@router.message(EditField.Traffic)
async def edit_traffic_done(message: Message, state: FSMContext):
    gb = TRAFFIC_MAP.get(message.text)
    if gb is None:
        await message.answer("Выбери трафик из кнопок.")
        return
    await state.update_data(traffic_gb=gb)
    await state.set_state(CreateUser.Confirm)
    await _show_confirm(message, state)


@router.callback_query(F.data == "cu:ed:expiry")
async def edit_expiry_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditField.Expiry)
    await call.message.answer("Выбери новый срок действия:", reply_markup=_expiry_kb())
    await call.answer()


@router.message(EditField.Expiry, F.text == "📅 Выбрать дату")
async def edit_expiry_custom(message: Message, state: FSMContext):
    await state.set_state(EditField.CustomDate)
    today = date.today()
    await message.answer("Выбери дату:", reply_markup=create_quick_buttons())
    await message.answer("📅", reply_markup=create_calendar(today.year, today.month))


@router.message(EditField.Expiry)
async def edit_expiry_done(message: Message, state: FSMContext):
    today = date.today()
    mapping = {
        "3 дня": today + timedelta(days=3),
        "7 дней": today + timedelta(days=7),
        "+ 1 год": date(today.year + 1, today.month, today.day),
    }
    expiry = mapping.get(message.text)
    if not expiry:
        await message.answer("Выбери срок из кнопок.")
        return
    await state.update_data(expiry_date=expiry)
    await state.set_state(CreateUser.Confirm)
    await _show_confirm(message, state)


@router.callback_query(EditField.CustomDate, F.data.startswith("cal:"))
async def edit_calendar_cb(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    action = parts[1]
    if action in ("prev", "next"):
        kb = create_calendar(int(parts[2]), int(parts[3]))
        await call.message.edit_reply_markup(reply_markup=kb)
        await call.answer()
        return
    if action == "ignore":
        await call.answer()
        return
    selected = process_calendar_selection(call.data)
    if selected:
        await state.update_data(expiry_date=selected)
        await call.message.delete()
        await state.set_state(CreateUser.Confirm)
        await _show_confirm(call.message, state)
    else:
        await call.answer("Выбери дату начиная с завтра.", show_alert=True)


# ─── Step 7: Confirm ─────────────────────────────────────────────────────────

@router.callback_query(CreateUser.Confirm, F.data == "cu:cancel")
async def confirm_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Действие отменено ❌", reply_markup=admin_keyboard())
    await call.answer()


@router.callback_query(CreateUser.Confirm, F.data == "cu:confirm")
async def confirm_create(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    nick = data["nick"]
    note = data.get("note", "")
    traffic_gb = data["traffic_gb"]
    expiry_date = _to_date(data["expiry_date"])

    import uuid as uuidlib, datetime
    traffic_bytes = traffic_gb * GB if traffic_gb > 0 else 0
    expiry_ms = int(datetime.datetime(
        expiry_date.year, expiry_date.month, expiry_date.day, 23, 59, 59
    ).timestamp() * 1000)

    settings = await database.get_all_settings()
    app_link_ios = settings.get("app_link_ios", "")
    msg = await call.message.answer("⏳ Создаю пользователя...")

    try:
        if data.get("bundle_mode"):
            # ── Bundle: создаём на 3 серверах с одним UUID ──
            bundle = data["bundle"]
            shared_uuid = str(uuidlib.uuid4())
            created = []
            errors = []

            for bi in bundle:
                suffix = f"_{bi['short']}_{bi['inbound_id']}"
                email = nick.replace(" ", "_") + suffix
                client = XUIClient(bi["url"], bi["username"], bi["password"])
                try:
                    if not await client.login():
                        errors.append(bi["display"])
                        continue
                    result = await client.create_client(
                        bi["inbound_id"], email, note, traffic_bytes, expiry_ms,
                        client_uuid=shared_uuid
                    )
                    if result:
                        created.append(bi["display"])
                    else:
                        errors.append(bi["display"])
                except Exception as e:
                    logger.error(f"bundle create_client {bi['display']}: {e}")
                    errors.append(bi["display"])
                finally:
                    await client.logout()

            if not created:
                await msg.edit_text("❌ Не удалось создать ни на одном сервере.")
                return

            client_uuid = shared_uuid
            redirect_url = _happ_redirect_url(client_uuid, "RED HAT")
            created_str = " + ".join(created)
            error_str = f"\n⚠️ Не создан на: {', '.join(errors)}" if errors else ""
            text = (
                f"👋 Привет, {nick}! Твой ВПН готов:\n"
                f"Серверы: {created_str}{error_str}\n\n"
                f"1️⃣ Открой Happ, Streisand или V2RayTun\n\n"
                f"2️⃣ [👉 Нажми здесь — ВПН добавится сам]({redirect_url})"
            )

        else:
            # ── Одиночный сервер (старая логика) ──
            server = data["server"]
            inbound_id = data.get("selected_inbound_id") or server["inbound_id"]
            flag = server["country_flag"]
            server_suffix = f"_{server['key']}{flag}"
            email = nick.replace(" ", "_") + server_suffix

            client = XUIClient(server["url"], server["username"], server["password"])
            if not await client.login():
                await msg.edit_text("❌ Не удалось подключиться к серверу.")
                return

            result = await client.create_client(inbound_id, email, note, traffic_bytes, expiry_ms)
            await client.logout()

            if not result:
                await msg.edit_text("❌ Не удалось создать пользователя.")
                return

            client_uuid = result["uuid"]
            redirect_url = _happ_redirect_url(client_uuid, server["button_name"])
            text = (
                f"👋 Привет, {nick}! Твой ВПН готов:\n\n"
                f"1️⃣ Открой Happ, Streisand или V2RayTun\n\n"
                f"2️⃣ [👉 Нажми здесь — ВПН добавится сам]({redirect_url})"
            )
            await database.set_setting("last_server_key", server["key"])

        await msg.edit_text(
            text,
            parse_mode="Markdown",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )

        sub_url = f"https://white.theredhat.su:8888/sub/{client_uuid}"
        sub_text = (
            f"Для V2RayTun / Hiddify и других приложений — ссылка-подписка:\n\n"
            f"<pre>{sub_url}</pre>"
        )
        await call.message.answer(
            sub_text,
            parse_mode="HTML",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    except Exception as e:
        logger.error(f"confirm_create error: {e}")
        await msg.edit_text(f"❌ Ошибка: {e}")
    finally:
        await state.clear()
