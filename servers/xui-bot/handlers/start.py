from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID

router = Router()

MINIAPP_URL = "https://vpn.theredhat.su"


def admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Новый"),
                KeyboardButton(text="📊 Стат"),
            ],
            [
                KeyboardButton(text="🔄 Xray"),
                KeyboardButton(text="🖥 Серверы"),
            ],
            [
                KeyboardButton(text="🔍 Поиск"),
                KeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=MINIAPP_URL)),
            ],
        ],
        resize_keyboard=True,
    )


async def show_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("·", reply_markup=admin_keyboard())


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return
    await show_main_menu(message, state)


@router.message(Command("cancel"))
@router.message(F.text.in_({"❌ Отмена", "🔙 Назад"}))
async def cmd_cancel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    current = await state.get_state()
    if current is None:
        # Нет активного состояния — показываем главное меню
        await show_main_menu(message, state)
    else:
        await state.clear()
        await show_main_menu(message, state)
