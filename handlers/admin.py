# handlers/admin.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_masterclasses, add_masterclass, delete_masterclass

router = Router()

@router.callback_query(lambda c: c.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить мастер-класс", callback_data="admin_add")],
            [InlineKeyboardButton(text="➖ Удалить мастер-класс", callback_data="admin_delete")],
            [InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")]
        ]
    )
    await callback.message.edit_text("⚙ Админ-панель", reply_markup=keyboard)
    await callback.answer()

# Пример обработчиков для добавления/удаления мастер-классов
@router.callback_query(lambda c: c.data == "admin_add")
async def add_masterclass(callback: types.CallbackQuery):
    # Логика добавления мастер-класса
    pass

@router.callback_query(lambda c: c.data == "admin_delete")
async def delete_masterclass(callback: types.CallbackQuery):
    # Логика удаления мастер-класса
    pass
