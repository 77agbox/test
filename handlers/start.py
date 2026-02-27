from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import add_subscriber, get_subscribers, unsubscribe
from keyboards import main_menu, bottom_kb
from config import ADMIN_ID
import asyncio
from aiogram import Bot

router = Router()


# ================= FSM =================

class MasterForm(StatesGroup):
    waiting_name = State()  # Состояние для ввода имени
    waiting_phone = State()  # Состояние для ввода телефона


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

@router.callback_query(lambda c: c.data == "send_broadcast")
async def send_broadcast(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    if callback.from_user.id == ADMIN_ID:  # Проверка на админа
        text = "📣 Новая рассылка! Мы вас ждем на новом мастер-классе!"
        subscribers = get_subscribers()  # Получаем подписчиков
        for user_id in subscribers:
            try:
                await bot.send_message(user_id, text)
                await asyncio.sleep(0.1)  # Задержка для безопасной рассылки
            except Exception as e:
                print(f"Ошибка при отправке сообщения {user_id}: {e}")
        await callback.message.answer("✅ Рассылка отправлена всем подписчикам.")
    else:
        await callback.message.answer("❌ Вы не админ, рассылку можно отправлять только администратору.")


# ================= АДМИН-ПАНЕЛЬ =================

@router.callback_query(lambda c: c.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:  # Проверка на админа
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить мастер-класс", callback_data="admin_add")],
                [InlineKeyboardButton(text="➖ Удалить мастер-класс", callback_data="admin_delete")],
                [InlineKeyboardButton(text="📢 Отправить рассылку", callback_data="send_broadcast")],
                [InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")]
            ]
        )
        await callback.message.edit_text("⚙ Админ-панель", reply_markup=keyboard)
    else:
        await callback.message.answer("❌ У вас нет прав для доступа к админ-панели.")
