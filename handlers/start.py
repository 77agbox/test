from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Text
from aiogram.types import ReplyKeyboardRemove

from database import add_subscriber, get_subscribers, unsubscribe
from keyboards import main_menu, bottom_kb
from config import ADMIN_ID

router = Router()

class MasterForm(StatesGroup):
    waiting_name = State()  # Состояние для ввода имени
    waiting_phone = State()  # Состояние для ввода телефона

@router.message(Text(equals="🏠 Начать заново"))
async def restart(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выберите раздел:",
        reply_markup=main_menu(is_admin=(message.from_user.id == ADMIN_ID)),
    )

@router.message(Text(equals="✉ Написать в поддержку"))
async def support_start(message: types.Message, state: FSMContext):
    await state.set_state(MasterForm.waiting_name)

    await message.answer(
        "Опишите проблему или вопрос.\n\n"
        "Сообщение будет отправлено администратору.",
        reply_markup=ReplyKeyboardRemove(),
    )

@router.message(MasterForm.waiting_name)
async def signup_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(MasterForm.waiting_phone)
    await message.answer("Введите номер телефона:")

@router.message(MasterForm.waiting_phone)
async def signup_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    add_subscriber(message.from_user.id, data['name'], message.text)

    await message.answer(
        "✅ Вы подписаны на мастер-классы.\nМы будем с вами на связи для дальнейших действий.",
        reply_markup=bottom_kb(is_admin=False),
    )
    await state.clear()
