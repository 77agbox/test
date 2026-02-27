from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import add_subscriber
from keyboards import main_menu, bottom_kb

router = Router()


# ================= FSM =================

class MasterForm(StatesGroup):
    waiting_name = State()  # Ввод имени
    waiting_phone = State()  # Ввод телефона


# ================= СТАРТ =================

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    name = message.from_user.first_name
    phone = "Не указан"

    add_subscriber(user_id, name, phone)

    await message.answer(
        "👋 <b>Здравствуйте!</b>\n\n"
        "Я бот Центра «Виктория».\n\n"
        "Выберите интересующий раздел:",
        parse_mode="HTML",
        reply_markup=main_menu(is_admin=False),
    )


# ================= НАЧАТЬ ЗАНОВО =================

@router.message(lambda m: m.text == "🏠 Начать заново")
async def restart(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Выберите раздел:",
        reply_markup=main_menu(is_admin=False),
    )


# ================= ПОДДЕРЖКА =================

@router.message(lambda m: m.text == "✉ Написать в поддержку")
async def support_start(message: types.Message, state: FSMContext):
    await state.set_state(MasterForm.waiting_name)

    await message.answer(
        "Опишите проблему или вопрос.\n\n"
        "Сообщение будет отправлено администратору.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# ================= СОХРАНЕНИЕ ДАННЫХ =================

@router.message(MasterForm.waiting_name)
async def signup_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(MasterForm.waiting_phone)
    await message.answer("Введите номер телефона:")


@router.message(MasterForm.waiting_phone)
async def signup_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # Сохраняем подписчика
    add_subscriber(message.from_user.id, data['name'], message.text)

    await message.answer(
        f"✅ Вы подписаны на мастер-классы.\nМы будем с вами на связи для дальнейших действий.",
        reply_markup=bottom_kb(is_admin=False),
    )
    await state.clear()
