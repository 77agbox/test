from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove

from config import ADMIN_ID
from database import add_subscriber, check_subscription
from keyboards import bottom_kb, main_menu

router = Router()


class MasterForm(StatesGroup):
    waiting_name = State()  # Состояние для ввода имени
    waiting_phone = State()  # Состояние для ввода телефона


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Обработчик команды /start. Сохраняет данные пользователя и выводит главное меню.
    """
    await state.clear()

    # Сохраняем данные пользователя (имя и телефон)
    user_id = message.from_user.id
    name = message.from_user.first_name
    phone = "Не указан"

    add_subscriber(user_id, name, phone)

    # Проверяем, подписан ли пользователь на рассылку
    is_subscribed = check_subscription(user_id)

    # Отправляем главное меню
    await message.answer(
        "👋 <b>Здравствуйте!</b>\n\n"
        "Я бот Центра «Виктория».\n\n"
        "Выберите интересующий раздел:",
        parse_mode="HTML",
        reply_markup=main_menu(is_admin=(message.from_user.id == ADMIN_ID)),
    )

    # Отправляем клавиатуру с правильной кнопкой подписки или отписки
    await message.answer(
        "Пожалуйста, выберите, что вы хотите сделать.",
        reply_markup=bottom_kb(
            is_subscribed=is_subscribed,
            is_admin=(message.from_user.id == ADMIN_ID),
        ),
    )


@router.message(lambda m: m.text == "🏠 Начать заново")
async def restart(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выберите раздел:",
        reply_markup=main_menu(is_admin=(message.from_user.id == ADMIN_ID)),
    )


@router.message(lambda m: m.text == "✉ Написать в поддержку")
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

    # Сохраняем подписчика
    add_subscriber(message.from_user.id, data["name"], message.text)

    await message.answer(
        "✅ Вы подписаны на мастер-классы.\nМы будем с вами на связи для дальнейших действий.",
        reply_markup=bottom_kb(is_admin=False),
    )
    await state.clear()
