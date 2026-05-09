import logging

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
from handlers.start import admin_keyboard

logger = logging.getLogger(__name__)
router = Router()


class SettingsState(StatesGroup):
    EditValue = State()


SETTINGS_LABELS = {
    "profile_prefix":   "Префикс",
    "profile_postfix":  "Постфикс",
    "message_footer":   "Текст под ссылкой",
    "app_name":         "Приложение",
    "app_link_ios":     "Ссылка iOS",
    "app_link_android": "Ссылка Android",
    "default_username": "Логин серверов",
    "default_password": "Пароль серверов",
}


def _truncate(s: str, n: int = 22) -> str:
    return s if len(s) <= n else s[:n - 2] + ".."


async def _settings_kb() -> InlineKeyboardMarkup:
    settings = await database.get_all_settings()
    buttons = []
    for key, label in SETTINGS_LABELS.items():
        val = _truncate(settings.get(key, ""))
        buttons.append([
            InlineKeyboardButton(
                text=f"{label}: {val}" if val else f"{label}: (пусто)",
                callback_data="cfg:ignore",
            ),
            InlineKeyboardButton(text="✏️", callback_data=f"cfg:edit:{key}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "⚙️ Профиль")
async def settings_entry(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    kb = await _settings_kb()
    await message.answer("⚙️ Настройки профиля:", reply_markup=kb)


@router.callback_query(F.data == "cfg:ignore")
async def cfg_ignore(call: CallbackQuery):
    await call.answer()


@router.callback_query(F.data.startswith("cfg:edit:"))
async def cfg_edit_start(call: CallbackQuery, state: FSMContext):
    setting_key = call.data.split(":", 2)[2]
    label = SETTINGS_LABELS.get(setting_key, setting_key)
    current = await database.get_setting(setting_key)

    await state.set_state(SettingsState.EditValue)
    await state.update_data(editing_key=setting_key, editing_label=label, msg_id=call.message.message_id)
    await call.message.answer(
        f"✏️ {label}\nТекущее значение: {current or '(пусто)'}\n\nВведи новое значение:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True,
        ),
    )
    await call.answer()


@router.message(SettingsState.EditValue, F.text == "❌ Отмена")
async def cfg_edit_cancel(message: Message, state: FSMContext):
    await state.clear()
    kb = await _settings_kb()
    await message.answer("Отменено.", reply_markup=admin_keyboard())
    await message.answer("⚙️ Настройки профиля:", reply_markup=kb)


@router.message(SettingsState.EditValue)
async def cfg_edit_save(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data["editing_key"]
    label = data["editing_label"]
    new_value = message.text.strip()

    await database.set_setting(key, new_value)
    await state.clear()

    kb = await _settings_kb()
    await message.answer(
        f"✅ {label} обновлён.",
        reply_markup=admin_keyboard(),
    )
    await message.answer("⚙️ Настройки профиля:", reply_markup=kb)
