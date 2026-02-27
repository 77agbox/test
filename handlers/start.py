from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import add_subscriber, get_subscribers, unsubscribe
from keyboards import main_menu, get_admin_panel_keyboard, bottom_kb  # Измените на правильный импорт
from config import ADMIN_ID
from aiogram import Bot  # Правильный импорт Bot

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

    # Проверяем, подписан ли пользователь на рассылку
    is_subscribed = get_subscribers().count(user_id) > 0

    # Отправляем главное меню
    await message.answer(
        "👋 <b>Здравствуйте!</b>\n\n"
        "Я бот Центра «Виктория».\n\n"
        "Выберите интересующий раздел:",
        parse_mode="HTML",
        reply_markup=main_menu(is_admin=(message.from_user.id == ADMIN_ID)),  # Главное меню с админ-кнопкой
    )

    # Отправляем клавиатуру с правильной кнопкой подписки или отписки
    await message.answer(
        "Пожалуйста, выберите, что вы хотите сделать.",
        reply_markup=bottom_kb(is_subscribed=is_subscribed, is_admin=(message.from_user.id == ADMIN_ID)),  # Передаем информацию о подписке
    )


@router.message(lambda m: m.text == "🏠 Начать заново")
async def restart(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Выберите раздел:",
        reply_markup=main_menu(is_admin=False),
    )


# ================= ПОДПИСАТЬСЯ И ОТПИСАТЬСЯ =================

@router.message(lambda m: m.text == "❌ Отписаться от рассылки")
async def unsubscribe_user(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    unsubscribe(user_id)

    await message.answer("❌ Вы отписались от рассылки.", reply_markup=bottom_kb(is_subscribed=False, is_admin=False))


@router.message(lambda m: m.text == "📢 Подписаться на рассылку")
async def subscribe_user(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.from_user.first_name
    phone = "Не указан"

    add_subscriber(user_id, name, phone)

    await message.answer("✅ Вы подписались на рассылку.", reply_markup=bottom_kb(is_subscribed=True, is_admin=False))


# ================= АДМИН-ПАНЕЛЬ =================

@router.callback_query(lambda c: c.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:  # Проверка на админа
        keyboard = admin_panel_kb()  # Клавиатура для админ-панели
        await callback.message.edit_text("⚙ Админ-панель", reply_markup=keyboard)
    else:
        await callback.message.answer("❌ У вас нет прав для доступа к админ-панели.")


# ================= РАССЫЛКА =================

@router.callback_query(lambda c: c.data == "send_broadcast")
async def send_broadcast(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    if callback.from_user.id == ADMIN_ID:
        text = "📣 Новая рассылка! Мы вас ждем на новом мастер-классе!"
        subscribers = get_subscribers()
        for user_id in subscribers:
            try:
                await bot.send_message(user_id, text)
            except Exception as e:
                print(f"Ошибка при отправке сообщения {user_id}: {e}")
        await callback.message.answer("✅ Рассылка отправлена всем подписчикам.")
    else:
        await callback.message.answer("❌ Вы не админ, рассылку можно отправлять только администратору.")

