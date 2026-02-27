from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import add_subscriber, get_subscribers, unsubscribe
from keyboards import main_menu, bottom_kb
from config import ADMIN_ID


router = Router()


# ================= FSM =================

class MasterForm(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


# ================= СТАРТ =================

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    # Сохраняем данные пользователя (имя и телефон)
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
    await state.set_state(MasterForm.waiting_message)

    await message.answer(
        "Опишите проблему или вопрос.\n\n"
        "Сообщение будет отправлено администратору.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# ================= ОТПРАВИТЬ СООБЩЕНИЕ В ПОДДЕРЖКУ =================

@router.message(MasterForm.waiting_message)
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
        reply_markup=bottom_kb(is_admin=False),
    )

    await state.clear()


# ================= ОТПИСАТЬСЯ ОТ РАССЫЛКИ =================

@router.message(lambda m: m.text == "❌ Отписаться от рассылки")
async def unsubscribe_user(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    unsubscribe(user_id)

    await message.answer("❌ Вы отписались от рассылки.", reply_markup=bottom_kb(is_admin=False))


# ================= ПОДПИСАТЬСЯ НА РАССЫЛКУ =================

@router.message(lambda m: m.text == "📢 Подписаться на рассылку")
async def subscribe_user(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.from_user.first_name
    phone = "Не указан"

    add_subscriber(user_id, name, phone)

    await message.answer("✅ Вы подписались на рассылку.", reply_markup=bottom_kb(is_admin=False))


# ================= РАССЫЛКА =================

@router.message(lambda m: m.text == "📢 Отправить рассылку")
async def send_broadcast(message: types.Message, state: FSMContext, bot: types.Bot):
    if message.from_user.id == ADMIN_ID:  # Проверка на админа
        text = "📣 Новая рассылка! Мы вас ждем на новом мастер-классе!"
        subscribers = get_subscribers()
        for user_id in subscribers:
            try:
                await bot.send_message(user_id, text)
                await asyncio.sleep(0.1)  # Задержка для безопасной рассылки
            except Exception as e:
                print(f"Ошибка при отправке сообщения {user_id}: {e}")
        await message.answer("✅ Рассылка отправлена всем подписчикам.")
    else:
        await message.answer("❌ Вы не админ, рассылку можно отправлять только администратору.")
