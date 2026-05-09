import asyncio
import json
import logging
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from database import get_all_servers, get_setting
from xui_client import XUIClient
from link_builder import build_link
from handlers.start import show_main_menu

router = Router()
logger = logging.getLogger(__name__)

GB = 1024 ** 3

PERIOD_OPTIONS = [
    ("7 дней", 7), ("1 месяц", 30), ("3 месяца", 90),
    ("6 месяцев", 180), ("1 год", 365), ("Не менять срок", 0),
]
TRAFFIC_OPTIONS = [
    ("10 ГБ", 10), ("300 ГБ", 300), ("500 ГБ", 500),
    ("1000 ГБ", 1000), ("Не менять трафик", 0),
]

_cache: dict[int, list[dict]] = {}


class SearchStates(StatesGroup):
    waiting_query = State()


# ─── Search ────────────────────────────────────────────────────────────────────

@router.message(F.text == "🔍 Поиск")
async def search_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(SearchStates.waiting_query)
    await message.answer("Введи запрос (имя, номер, часть email):")


@router.message(SearchStates.waiting_query)
async def search_execute(message: Message, state: FSMContext):
    query = message.text.strip().lower()
    await state.clear()

    if not query:
        await show_main_menu(message, state)
        return

    status_msg = await message.answer("⏳ Ищу по всем серверам...")

    servers = await get_all_servers()
    username = await get_setting("default_username")
    password = await get_setting("default_password")

    results: list[dict] = []

    async def search_server(server: dict):
        client = XUIClient(server["url"], username, password)
        try:
            if not await client.login():
                return
            resp = await client._session.get(f"{client.url}/panel/api/inbounds/list")
            data = await resp.json()
            for inb in data.get("obj", []):
                try:
                    inb_settings = json.loads(inb.get("settings", "{}"))
                except Exception:
                    continue
                for c in inb_settings.get("clients", []):
                    email = c.get("email", "")
                    if query in email.lower():
                        results.append({
                            "server_key":     server["key"],
                            "server_url":     server["url"],
                            "server_name":    server["button_name"],
                            "inbound_id":     inb["id"],
                            "inbound_remark": inb.get("remark") or str(inb["port"]),
                            "port":           inb["port"],
                            "email":          email,
                            "uuid":           c.get("id", ""),
                            "inbound_info":   inb,
                            "client_dict":    c,
                        })
        except Exception as e:
            logger.warning(f"Search error on {server['key']}: {e}")
        finally:
            await client.logout()

    await asyncio.gather(*[search_server(s) for s in servers])

    if not results:
        await status_msg.edit_text(f"❌ По запросу «{message.text.strip()}» ничего не найдено.")
        return

    _cache[message.from_user.id] = results

    buttons = []
    for i, r in enumerate(results):
        label = f"{r['email']}  ·  {r['server_key']}  :{r['port']}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"sr:{i}")])

    # Кнопка продления — одна на уникальный UUID
    uuid_groups: dict[str, list[dict]] = {}
    for r in results:
        uuid_groups.setdefault(r["uuid"], []).append(r)

    for uuid, group in uuid_groups.items():
        email = group[0]["email"]
        label = f"🔄 Продлить «{email}» ({len(group)} серв.)"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"rn:{uuid}")])

    await status_msg.edit_text(
        f"🔍 Найдено совпадений: <b>{len(results)}</b>\nТапни — получишь ссылку:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("sr:"))
async def search_result_tap(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    idx = int(callback.data.split(":")[1])
    results = _cache.get(callback.from_user.id, [])

    if idx >= len(results):
        await callback.answer("Результат устарел — выполни поиск заново.", show_alert=True)
        return

    r = results[idx]
    link = build_link(
        inbound_info=r["inbound_info"],
        client_uuid=r["uuid"],
        client_password="",
        profile_name=r["email"],
        panel_url=r["server_url"],
    )
    text = (
        f"📋 <b>{r['email']}</b>\n"
        f"Сервер: {r['server_name']}\n"
        f"Инбаунд: {r['inbound_remark']} (:{r['port']})\n\n"
        f"<pre>{link}</pre>"
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# ─── Renewal step 1: выбор срока ──────────────────────────────────────────────

@router.callback_query(F.data.startswith("rn:"))
async def renew_period_select(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    uuid = callback.data[3:]
    results = _cache.get(callback.from_user.id, [])
    group = [r for r in results if r["uuid"] == uuid]
    if not group:
        await callback.answer("Кэш устарел — сделай поиск заново.", show_alert=True)
        return

    email = group[0]["email"]
    rows, row = [], []
    for label, days in PERIOD_OPTIONS:
        row.append(InlineKeyboardButton(text=label, callback_data=f"rp:{uuid}:{days}"))
        if len(row) == 3:
            rows.append(row); row = []
    if row:
        rows.append(row)

    await callback.message.edit_text(
        f"🔄 <b>Продление «{email}»</b> · {len(group)} серв.\n\n"
        f"Шаг 1/2 — выбери <b>срок</b>:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Renewal step 2: выбор трафика ────────────────────────────────────────────

@router.callback_query(F.data.startswith("rp:"))
async def renew_traffic_select(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    _, uuid, days_str = callback.data.split(":", 2)
    days = int(days_str)
    period_label = next((l for l, d in PERIOD_OPTIONS if d == days), f"{days} дн.")

    rows, row = [], []
    for label, gb in TRAFFIC_OPTIONS:
        row.append(InlineKeyboardButton(text=label, callback_data=f"rt:{uuid}:{days}:{gb}"))
        if len(row) == 3:
            rows.append(row); row = []
    if row:
        rows.append(row)

    await callback.message.edit_text(
        f"Срок: <b>{period_label}</b>\n\n"
        f"Шаг 2/2 — выбери <b>трафик</b>:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Renewal step 3: подтверждение ────────────────────────────────────────────

@router.callback_query(F.data.startswith("rt:"))
async def renew_confirm_screen(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    _, uuid, days_str, gb_str = callback.data.split(":", 3)
    days, traffic_gb = int(days_str), int(gb_str)

    period_label  = next((l for l, d in PERIOD_OPTIONS  if d == days),       f"{days} дн.")
    traffic_label = next((l for l, g in TRAFFIC_OPTIONS if g == traffic_gb), f"{traffic_gb} ГБ")

    expiry_line = ""
    if days > 0:
        new_ts = int(datetime.now(timezone.utc).timestamp() * 1000) + days * 86400 * 1000
        expiry_line = f"\n⏱ Новый срок до: <b>{datetime.fromtimestamp(new_ts / 1000).strftime('%d.%m.%Y')}</b>"

    results = _cache.get(callback.from_user.id, [])
    group   = [r for r in results if r["uuid"] == uuid]
    email   = group[0]["email"] if group else uuid[:8]

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"rc:{uuid}:{days}:{traffic_gb}"),
        InlineKeyboardButton(text="❌ Отмена",      callback_data="rcancel"),
    ]])
    await callback.message.edit_text(
        f"🔄 <b>Подтверждение «{email}»</b>\n"
        f"Серверов: {len(group)}\n\n"
        f"⏱ Срок: <b>{period_label}</b>{expiry_line}\n"
        f"📦 Трафик: <b>{traffic_label}</b>\n\n"
        f"Применить ко всем серверам?",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Renewal: выполнение ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("rc:"))
async def renew_execute(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    _, uuid, days_str, gb_str = callback.data.split(":", 3)
    days, traffic_gb = int(days_str), int(gb_str)

    if days == 0 and traffic_gb == 0:
        await callback.answer("Ничего не выбрано — нечего менять.", show_alert=True)
        return

    await callback.message.edit_text("⏳ Обновляю на всех серверах...")
    await callback.answer()

    new_expiry_ms: int | None = None
    if days > 0:
        new_expiry_ms = int(datetime.now(timezone.utc).timestamp() * 1000) + days * 86400 * 1000

    new_traffic_bytes: int | None = None
    if traffic_gb == -1:
        new_traffic_bytes = 0
    elif traffic_gb > 0:
        new_traffic_bytes = traffic_gb * GB

    results  = _cache.get(callback.from_user.id, [])
    group    = [r for r in results if r["uuid"] == uuid]
    username = await get_setting("default_username")
    password = await get_setting("default_password")

    async def update_one(r: dict) -> tuple[str, bool]:
        xui = XUIClient(r["server_url"], username, password)
        try:
            if not await xui.login():
                return r["server_key"], False
            clients = await xui.get_all_clients(r["inbound_id"])
            client_dict = next((c for c in clients if c.get("id") == uuid), None)
            if client_dict is None:
                return r["server_key"], False
            ok = await xui.update_client_params(
                r["inbound_id"], uuid, client_dict,
                new_expiry_ms=new_expiry_ms,
                new_traffic_bytes=new_traffic_bytes,
            )
            return r["server_key"], ok
        except Exception as e:
            logger.error(f"Renewal error on {r['server_key']}: {e}")
            return r["server_key"], False
        finally:
            await xui.logout()

    server_results = await asyncio.gather(*[update_one(r) for r in group])

    email    = group[0]["email"] if group else uuid[:8]
    ok_count = sum(1 for _, ok in server_results if ok)

    period_label  = next((l for l, d in PERIOD_OPTIONS  if d == days),       f"{days} дн.")
    traffic_label = next((l for l, g in TRAFFIC_OPTIONS if g == traffic_gb), f"{traffic_gb} ГБ")

    lines = "\n".join(f"  {'✓' if ok else '✗'} {key}" for key, ok in server_results)

    changes = []
    if days > 0:
        changes.append(f"⏱ Срок: {period_label} → до {datetime.fromtimestamp(new_expiry_ms / 1000).strftime('%d.%m.%Y')}")
    if traffic_gb != 0:
        changes.append(f"📦 Трафик: {traffic_label}")

    await callback.message.edit_text(
        f"{'✅' if ok_count == len(group) else '⚠️'} <b>«{email}»</b> — {ok_count}/{len(group)} серв.\n\n"
        f"{lines}\n\n"
        + "\n".join(changes) + "\n\n"
        + "💬 Скажи клиенту: в Happ нажми «Обновить подписку»",
        parse_mode="HTML",
    )


# ─── Cancel ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "rcancel")
async def renew_cancel(callback: CallbackQuery):
    await callback.message.edit_text("❌ Продление отменено.")
    await callback.answer()
