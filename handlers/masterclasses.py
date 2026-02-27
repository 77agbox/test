from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database import get_masterclasses
from config import ADMIN_ID
from keyboards import main_menu

router = Router()


# ================= FSM =================

class MasterForm(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


# ================= ОТКРЫТЬ СПИСОК =================

@router.callback_query(lambda c: c.data == "m_master")
async def show_masterclasses(callback: types.CallbackQuery):
    rows = get_masterclasses()

    if not rows:
        await callback.message.edit_text("Сейчас нет доступных мастер-классов.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=row[1],  # title
                    callback_data=f"mc_{row[0]}"  # id
                )
            ]
            for row in rows
        ] + [[InlineKeyboardButton(text="⬅ В меню", callback_data="back_main")]]
    )

    await callback.message.edit_text(
        "🎨 Доступные мастер-классы:",
        reply_markup=keyboard
    )

    await callback.answer()


# ================= КАРТОЧКА МК =================

@router.callback_query(lambda c: c.data.startswith("mc_"))
async def show_mastercard(callback: types.CallbackQuery, state: FSMContext):
    mc_id = int(callback.data.split("_")[1])

    rows = get_masterclasses()
    mc = next((row for row in rows if row[0] == mc_id), None)

    if not mc:
        await callback.answer("Не найдено")
        return

    text = (
        f"<b>{mc[1]}</b>\n\n"
        f"📍 {mc[2]}\n"
        f"👩‍🏫 {mc[4]}\n"
        f"🕒 {mc[5]}\n"
        f"💰 {mc[6]}\n\n"
        f"{mc[3]}\n\n"
        f"{mc[7]}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Записаться", callback_data=f"signup_{mc_id}")],
            [InlineKeyboardButton(text="⬅ Назад", callback_data="m_master")]
        ]
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )

    await callback.answer()


# ================= ЗАПИСЬ =================

@router.callback_query(lambda c: c.data.startswith("signup_"))
async def signup_start(callback: types.CallbackQuery, state: FSMContext):
    mc_id = int(callback.data.split("_")[1])
    await state.update_data(mc_id=mc_id)

    await state.set_state(MasterForm.waiting_name)

    await callback.message.answer("Введите ваше имя:")
    await callback.answer()


@router.message(MasterForm.waiting_name)
async def signup_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(MasterForm.waiting_phone)
    await message.answer("Введите номер телефона:")


@router.message(MasterForm.waiting_phone)
async def signup_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mc_id = data["mc_id"]

    rows = get_masterclasses()
    mc = next((row for row in rows if row[0] == mc_id), None)

    if not mc:
        await message.answer("Ошибка.")
        await state.clear()
        return

    text = (
        "📥 Новая запись на мастер-класс\n\n"
        f"Мастер-класс: {mc[1]}\n"
        f"Дата: {mc[5]}\n"
        f"Стоимость: {mc[6]}\n\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {message.text}\n\n"
        f"TG: @{message.from_user.username or 'нет'}\n"
        f"ID: {message.from_user.id}"
    )

    await message.bot.send_message(
        ADMIN_ID,
        text
    )

    await message.answer(
        "✅ Вы записаны!\n"
        "Администратор свяжется с вами.",
        reply_markup=main_menu(is_admin=(message.from_user.id == ADMIN_ID))
    )

    await state.clear()
