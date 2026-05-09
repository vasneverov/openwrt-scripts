import asyncio
import logging
from datetime import datetime

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


class AddServer(StatesGroup):
    AKey = State()
    AName = State()
    AFlag = State()
    AUrl = State()
    AInbound = State()


class RestartXray(StatesGroup):
    SelectServer = State()
    Confirm1 = State()
    Confirm2 = State()


class DeleteServer(StatesGroup):
    SelectServer = State()
    Confirm = State()


class CloneInbound(StatesGroup):
    SelectServer = State()
    SelectInbound = State()
    EnterName = State()
    EnterPort = State()


def _back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True,
    )


def _admin_servers_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="adm:add"),
            InlineKeyboardButton(text="📋 Список",   callback_data="adm:list"),
        ],
        [
            InlineKeyboardButton(text="❌ Удалить",          callback_data="adm:del"),
            InlineKeyboardButton(text="🔄 Перезагрузить Xray", callback_data="adm:restart"),
        ],
        [
            InlineKeyboardButton(text="📋 Клонировать инбаунд", callback_data="adm:clone"),
        ],
    ])


def _servers_select_kb(servers: list[dict], prefix: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=s["button_name"], callback_data=f"{prefix}:{s['key']}")]
        for s in servers
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Entry ────────────────────────────────────────────────────────────────────

@router.message(F.text == "🖥 Серверы")
async def manage_servers(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("⚙️ Управление серверами:", reply_markup=_admin_servers_kb())


@router.callback_query(F.data == "adm:cancel")
async def adm_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Отменено.", reply_markup=admin_keyboard())
    await call.answer()


# ─── List Servers ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:list")
async def adm_list(call: CallbackQuery, state: FSMContext):
    servers = await database.get_all_servers()
    if not servers:
        await call.answer("Серверов нет.", show_alert=True)
        return
    lines = ["📋 Серверы:\n"]
    for s in servers:
        lines.append(
            f"• {s['button_name']}\n"
            f"  URL: {s['url']}\n"
            f"  Inbound ID: {s['inbound_id']}\n"
            f"  Ключ: {s['key']}"
        )
    await call.message.answer("\n\n".join(lines))
    await call.answer()


# ─── Add Server ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:add")
async def adm_add_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddServer.AKey)
    await call.message.answer(
        "Название сервера (пример: poland_3):",
        reply_markup=_back_kb(),
    )
    await call.answer()


async def _go_back_add(message: Message, state: FSMContext, prev_state, text: str):
    await state.set_state(prev_state)
    await message.answer(text, reply_markup=_back_kb())


@router.message(AddServer.AKey, F.text == "🔙 Назад")
async def add_key_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Управление серверами:", reply_markup=admin_keyboard())
    await message.answer("⚙️", reply_markup=_admin_servers_kb())


@router.message(AddServer.AKey)
async def add_key(message: Message, state: FSMContext):
    key = message.text.strip()
    if not key.replace("_", "").isalnum():
        await message.answer("Ключ должен содержать только латиницу и _.")
        return
    if await database.server_exists(key):
        await message.answer("Сервер с таким ключом уже существует.")
        return
    await state.update_data(key=key)
    await state.set_state(AddServer.AName)
    await message.answer("Введи название кнопки (пример: 🇵🇱 Польша-3):", reply_markup=_back_kb())


@router.message(AddServer.AName, F.text == "🔙 Назад")
async def add_name_back(message: Message, state: FSMContext):
    await state.set_state(AddServer.AKey)
    await message.answer("Введи ключ сервера:", reply_markup=_back_kb())


@router.message(AddServer.AName)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(button_name=message.text.strip())
    await state.set_state(AddServer.AFlag)
    await message.answer("Введи эмодзи флага (пример: 🇵🇱):", reply_markup=_back_kb())


@router.message(AddServer.AFlag, F.text == "🔙 Назад")
async def add_flag_back(message: Message, state: FSMContext):
    await state.set_state(AddServer.AName)
    await message.answer("Введи название кнопки:", reply_markup=_back_kb())


@router.message(AddServer.AFlag)
async def add_flag(message: Message, state: FSMContext):
    await state.update_data(country_flag=message.text.strip())
    await state.set_state(AddServer.AUrl)
    await message.answer("Введи URL панели (пример: https://pl3.domain.com:2053):", reply_markup=_back_kb())


@router.message(AddServer.AUrl, F.text == "🔙 Назад")
async def add_url_back(message: Message, state: FSMContext):
    await state.set_state(AddServer.AFlag)
    await message.answer("Введи эмодзи флага:", reply_markup=_back_kb())


def _parse_base_url(raw: str) -> str:
    """Из любой ссылки на панель вырезать базовый URL для API.
    Пример: https://host:5050/5050/panel/inbounds → https://host:5050/5050
    """
    raw = raw.strip().rstrip("/")
    # Обрезаем всё начиная с /panel/
    if "/panel/" in raw:
        raw = raw.split("/panel/")[0]
    elif raw.endswith("/panel"):
        raw = raw[: -len("/panel")]
    return raw


@router.message(AddServer.AUrl)
async def add_url(message: Message, state: FSMContext):
    base_url = _parse_base_url(message.text)
    await state.update_data(url=base_url)
    await state.set_state(AddServer.AInbound)
    await message.answer(
        f"URL сохранён: <code>{base_url}</code>\n\nInbound ID — номер inbound из панели 3x-ui (раздел Inbounds, левая колонка):",
        reply_markup=_back_kb(),
        parse_mode="HTML",
    )


@router.message(AddServer.AInbound, F.text == "🔙 Назад")
async def add_inbound_back(message: Message, state: FSMContext):
    await state.set_state(AddServer.AUrl)
    await message.answer("Введи URL панели:", reply_markup=_back_kb())


@router.message(AddServer.AInbound)
async def add_inbound(message: Message, state: FSMContext):
    try:
        inbound_id = int(message.text.strip())
    except ValueError:
        await message.answer("Inbound ID должен быть числом.")
        return

    await state.update_data(inbound_id=inbound_id)
    data = await state.get_data()

    username = await database.get_setting("default_username")
    password = await database.get_setting("default_password")
    await state.update_data(username=username, password=password)

    msg = await message.answer("🔌 Подключаюсь.")
    client = XUIClient(data["url"], username, password)

    async def animate():
        dots = [".", "..", "...", "...."]
        i = 0
        while True:
            await asyncio.sleep(1)
            try:
                await msg.edit_text(f"🔌 Подключаюсь{dots[i % len(dots)]}")
            except Exception:
                break
            i += 1

    anim_task = asyncio.create_task(animate())
    ok = await client.test_connection()
    anim_task.cancel()

    if ok:
        await database.add_server(
            data["key"], data["button_name"], data["country_flag"],
            data["url"], username, password, inbound_id,
        )
        await msg.edit_text("✅ Сервер добавлен!")
        await state.clear()
        await message.answer("Выбери действие:", reply_markup=admin_keyboard())
    else:
        await msg.edit_text(
            "❌ Не удалось подключиться. Проверь данные.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔄 Повторить", callback_data="adm:retry_connect"),
                InlineKeyboardButton(text="❌ Отмена",    callback_data="adm:cancel"),
            ]]),
        )


@router.callback_query(F.data == "adm:retry_connect")
async def adm_retry_connect(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    msg = await call.message.answer("⏳ Повторяю попытку...")
    username = data.get("username") or await database.get_setting("default_username")
    password = data.get("password") or await database.get_setting("default_password")
    client = XUIClient(data["url"], username, password)
    ok = await client.test_connection()
    if ok:
        await database.add_server(
            data["key"], data["button_name"], data["country_flag"],
            data["url"], data["username"], data["password"], data["inbound_id"],
        )
        await msg.edit_text("✅ Сервер добавлен!")
        await state.clear()
    else:
        await msg.edit_text(
            "❌ Всё ещё не удаётся подключиться.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔄 Повторить", callback_data="adm:retry_connect"),
                InlineKeyboardButton(text="❌ Отмена",    callback_data="adm:cancel"),
            ]]),
        )


# ─── Delete Server ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:del")
async def adm_del_start(call: CallbackQuery, state: FSMContext):
    servers = await database.get_all_servers()
    if not servers:
        await call.answer("Нет серверов для удаления.", show_alert=True)
        return
    await state.set_state(DeleteServer.SelectServer)
    await call.message.edit_text(
        "Выбери сервер для удаления:",
        reply_markup=_servers_select_kb(servers, "adm:del_srv"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm:del_srv:"))
async def adm_del_confirm(call: CallbackQuery, state: FSMContext):
    server_key = call.data.split(":", 2)[2]
    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return
    await state.update_data(del_server_key=server_key, del_server_name=server["button_name"])
    await state.set_state(DeleteServer.Confirm)
    await call.message.edit_text(
        f"Удалить сервер {server['button_name']}?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Удалить", callback_data="adm:del_confirm"),
            InlineKeyboardButton(text="❌ Отмена",  callback_data="adm:cancel"),
        ]]),
    )
    await call.answer()


@router.callback_query(DeleteServer.Confirm, F.data == "adm:del_confirm")
async def adm_del_execute(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await database.deactivate_server(data["del_server_key"])
    await call.message.edit_text(f"✅ Сервер {data['del_server_name']} удалён.")
    await state.clear()
    await call.answer()


# ─── Restart Xray ─────────────────────────────────────────────────────────────

@router.message(F.text == "🔄 Xray")
async def adm_restart_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    servers = await database.get_all_servers()
    if not servers:
        await message.answer("Нет активных серверов.")
        return
    now_str = datetime.now().strftime("%d.%m.%y %H:%M")
    await message.answer(
        f"🔄 <b>Перезапуск Xray на всех серверах</b> · {now_str}\n\n"
        f"Серверов: {len(servers)}\nСоединения прервутся на 3–5 секунд на каждом.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Перезапустить все", callback_data="adm:rst_all"),
            InlineKeyboardButton(text="❌ Отмена",            callback_data="adm:cancel"),
        ]]),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm:rst_all")
async def adm_restart_all_execute(call: CallbackQuery, state: FSMContext):
    await call.answer()
    servers = await database.get_all_servers()
    await call.message.edit_text(f"⏳ Перезапускаю Xray на {len(servers)} серверах...")

    async def restart_one(server: dict):
        xui = XUIClient(server["url"], server["username"], server["password"])
        try:
            if not await xui.login():
                return server["button_name"], False
            ok = await xui.restart_xray()
            return server["button_name"], ok
        except Exception as e:
            logger.error(f"restart_all {server['key']}: {e}")
            return server["button_name"], False
        finally:
            await xui.logout()

    results = await asyncio.gather(*[restart_one(s) for s in servers])

    ok_count = sum(1 for _, ok in results if ok)
    now_str = datetime.now().strftime("%H:%M:%S")
    lines = [f"🔄 <b>Xray перезапущен</b> · {now_str}\n"]
    for name, ok in results:
        lines.append(f"{'✅' if ok else '❌'} {name}")
    lines.append(f"\n<b>Итого: {ok_count}/{len(servers)}</b>")

    await call.message.edit_text("\n".join(lines), parse_mode="HTML")
    await state.clear()


# ─── Clone Inbound ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:clone")
async def adm_clone_start(call: CallbackQuery, state: FSMContext):
    servers = await database.get_all_servers()
    if not servers:
        await call.answer("Нет серверов.", show_alert=True)
        return
    await state.set_state(CloneInbound.SelectServer)
    await call.message.edit_text(
        "Выбери сервер:",
        reply_markup=_servers_select_kb(servers, "adm:clone_srv"),
    )
    await call.answer()


@router.callback_query(CloneInbound.SelectServer, F.data.startswith("adm:clone_srv:"))
async def adm_clone_select_inbound(call: CallbackQuery, state: FSMContext):
    server_key = call.data.split(":", 2)[2]
    server = await database.get_server(server_key)
    if not server:
        await call.answer("Сервер не найден.", show_alert=True)
        return

    await call.message.edit_text("⏳ Загружаю инбаунды...")
    xui = XUIClient(server["url"], server["username"], server["password"])
    try:
        if not await xui.login():
            await call.message.edit_text("❌ Не удалось подключиться.")
            return
        inbounds = await xui.get_inbounds_list()
    finally:
        await xui.logout()

    if not inbounds:
        await call.message.edit_text("❌ Инбаундов нет.")
        return

    await state.update_data(clone_server=server, clone_inbounds=inbounds)
    await state.set_state(CloneInbound.SelectInbound)

    buttons = [
        [InlineKeyboardButton(
            text=f"{ib.get('remark', '?')} :{ib.get('port', '?')}",
            callback_data=f"adm:clone_ib:{ib['id']}"
        )]
        for ib in inbounds
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel")])
    await call.message.edit_text(
        "Выбери инбаунд для клонирования:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await call.answer()


@router.callback_query(CloneInbound.SelectInbound, F.data.startswith("adm:clone_ib:"))
async def adm_clone_enter_name(call: CallbackQuery, state: FSMContext):
    inbound_id = int(call.data.split(":", 2)[2])
    data = await state.get_data()
    inbounds = data.get("clone_inbounds", [])
    source = next((ib for ib in inbounds if ib["id"] == inbound_id), None)
    if not source:
        await call.answer("Инбаунд не найден.", show_alert=True)
        return
    await state.update_data(clone_source=source)
    await state.set_state(CloneInbound.EnterName)
    await call.message.answer(
        f"Клонирую: {source.get('remark')} :{source.get('port')}\n\nВведи название нового инбаунда:",
        reply_markup=_back_kb(),
    )
    await call.answer()


@router.message(CloneInbound.EnterName, F.text == "🔙 Назад")
async def adm_clone_name_back(message: Message, state: FSMContext):
    data = await state.get_data()
    server = data.get("clone_server")
    inbounds = data.get("clone_inbounds", [])
    await state.set_state(CloneInbound.SelectInbound)
    buttons = [
        [InlineKeyboardButton(
            text=f"{ib.get('remark', '?')} :{ib.get('port', '?')}",
            callback_data=f"adm:clone_ib:{ib['id']}"
        )]
        for ib in inbounds
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel")])
    await message.answer(
        "Выбери инбаунд для клонирования:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.message(CloneInbound.EnterName)
async def adm_clone_enter_port(message: Message, state: FSMContext):
    await state.update_data(clone_name=message.text.strip())
    await state.set_state(CloneInbound.EnterPort)
    await message.answer("Введи порт нового инбаунда:", reply_markup=_back_kb())


@router.message(CloneInbound.EnterPort, F.text == "🔙 Назад")
async def adm_clone_port_back(message: Message, state: FSMContext):
    await state.set_state(CloneInbound.EnterName)
    await message.answer("Введи название нового инбаунда:", reply_markup=_back_kb())


@router.message(CloneInbound.EnterPort)
async def adm_clone_execute(message: Message, state: FSMContext):
    try:
        port = int(message.text.strip())
    except ValueError:
        await message.answer("Порт должен быть числом.")
        return

    data = await state.get_data()
    server = data["clone_server"]
    source = data["clone_source"]
    name = data["clone_name"]

    msg = await message.answer("⏳ Создаю инбаунд...")
    xui = XUIClient(server["url"], server["username"], server["password"])
    try:
        if not await xui.login():
            await msg.edit_text("❌ Не удалось подключиться.")
            return
        new_id = await xui.clone_inbound(source, name, port)
        if new_id:
            await database.update_server_inbound(server["key"], new_id)
            await database.set_setting("last_server_key", server["key"])
            await msg.edit_text(
                f"✅ Инбаунд «{name}» создан на порту {port}.\n"
                f"Новые пользователи будут создаваться в нём."
            )
        else:
            await msg.edit_text("❌ Не удалось создать инбаунд.")
    finally:
        await xui.logout()
        await state.clear()
    await message.answer("Выбери действие:", reply_markup=admin_keyboard())
