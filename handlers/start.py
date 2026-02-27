from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from keyboards import main_menu

router = Router()


class SupportForm(StatesGroup):
    waiting_message = State()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 <b>Здравствуйте!</b>\n\n"
        "Я бот Центра «Виктория».\n\n"
        "Выберите интересующий раздел:",
        parse_mode="HTML",
        reply_markup=main_menu(is_admin=(message.from_user.id == ADMIN_ID)),
    )


@router.callback_query(lambda c: c.data == "back_main")
async def back_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Выберите раздел:",
        reply_markup=main_menu(is_admin=(callback.from_user.id == ADMIN_ID)),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "support_start")
async def support_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SupportForm.waiting_message)
    await callback.message.edit_text(
        "✉ Напишите ваш вопрос одним сообщением.\n\n"
        "Мы передадим его администратору.",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")]]
        ),
    )
    await callback.answer()


@router.message(SupportForm.waiting_message)
async def support_send(message: types.Message, state: FSMContext):
    text = (
        "📩 Новое обращение в поддержку\n\n"
        f"Сообщение: {message.text}\n\n"
        f"TG: @{message.from_user.username or 'нет'}\n"
        f"ID: {message.from_user.id}"
    )
    await message.bot.send_message(ADMIN_ID, text)

    await message.answer(
        "✅ Ваше сообщение отправлено.\nВыберите раздел:",
        reply_markup=main_menu(is_admin=(message.from_user.id == ADMIN_ID)),
    )
    await state.clear()
