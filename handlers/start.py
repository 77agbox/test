from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from keyboards import main_menu, bottom_kb

router = Router()


# ================= FSM ПОДДЕРЖКИ =================

class SupportForm(StatesGroup):
    waiting_message = State()


# ================= СТАРТ =================

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "👋 <b>Здравствуйте!</b>\n\n"
        "Я бот Центра «Виктория».\n\n"
        "Выберите интересующий раздел:",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# ================= НАЧАТЬ ЗАНОВО =================

@router.message(lambda m: m.text == "🏠 Начать заново")
async def restart(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Выберите раздел:",
        reply_markup=main_menu(),
    )


# ================= ПОДДЕРЖКА =================

@router.message(lambda m: m.text == "✉ Написать в поддержку")
async def support_start(message: types.Message, state: FSMContext):
    await state.set_state(SupportForm.waiting_message)

    await message.answer(
        "Опишите проблему или вопрос.\n\n"
        "Сообщение будет отправлено администратору.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@router.message(SupportForm.waiting_message)
async def support_send(message: types.Message, state: FSMContext):
    username_link = (
        f'<a href="https://t.me/{message.from_user.username}">@{message.from_user.username}</a>'
        if message.from_user.username
        else "без username"
    )

    await message.bot.send_message(
        ADMIN_ID,
        f"📩 <b>Сообщение в поддержку</b>\n\n"
        f"<b>От:</b> {message.from_user.full_name}\n"
        f"<b>Профиль:</b> {username_link}\n"
        f"<b>TG ID:</b> {message.from_user.id}\n\n"
        f"<b>Сообщение:</b>\n{message.text}",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    await message.answer(
        "✅ Ваше сообщение отправлено администратору.\n"
        "Мы свяжемся с вами при необходимости.",
        reply_markup=bottom_kb(),
    )

    await state.clear()


# ================= НАЗАД В МЕНЮ =================

@router.callback_query(lambda c: c.data == "back_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.edit_text(
        "Выберите раздел:",
        reply_markup=main_menu(),
    )
    await callback.answer()
