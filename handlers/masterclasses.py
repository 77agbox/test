from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from config import ADMIN_ID
from keyboards import bottom_kb

router = Router()


# ===== ДАННЫЕ МАСТЕР-КЛАССОВ =====

MASTERCLASSES = [
    {
        "title": "Шерстяная акварель",
        "place": "Щербинка",
        "description": "Создание шерстяных картин — приятный творческий процесс. Сделайте уникальное украшение для вашего интерьера.",
        "teacher": "Лапина Светлана Юрьевна",
        "date": "9 марта 12:00–14:00, Каб.18",
        "price": "1 200 руб.",
        "link": "https://t.me/dyutsvictory/3815",
    },
    {
        "title": "Сумочка для телефона",
        "place": "Щербинка",
        "description": "Практичный аксессуар для телефона, карт и мелочей. Подходит для прогулок и отдыха.",
        "teacher": "Кузманович Ольга Вениаминовна",
        "date": "21 марта и 11 апреля 15:00–17:00, Каб.30",
        "price": "800 руб.",
        "link": "https://t.me/dyutsvictory/3816",
    },
    {
        "title": "Авторская керамика",
        "place": "Щербинка",
        "description": "Создание уникального изделия из глины с обжигом и росписью.",
        "teacher": "Латыпова Гульшат Габдулхаевна",
        "date": "4 марта 17:30–19:00 и 19:00–20:30, Каб.2",
        "price": "Дети — 2 000 руб.\nВзрослые — 2 500 руб.",
        "link": "https://t.me/dyutsvictory/3817",
    },
]


# ===== FSM =====
class MasterForm(StatesGroup):
    select = State()
    name = State()
    phone = State()


# ===== Список мастер-классов =====
@router.callback_query(lambda c: c.data == "m_master")
async def show_masterclasses(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{m['place']} — {m['title']}",
                    callback_data=f"mc_{i}"
                )
            ]
            for i, m in enumerate(MASTERCLASSES)
        ]
    )

    await state.set_state(MasterForm.select)
    await callback.message.edit_text(
        "🎨 <b>Мастер-классы</b>\n\nВыберите мероприятие:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    await callback.answer()


# ===== Карточка =====
@router.callback_query(lambda c: c.data.startswith("mc_"))
async def show_mastercard(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    mc = MASTERCLASSES[index]

    await state.update_data(selected_mc=mc)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Записаться",
                    callback_data="mc_signup"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔗 Подробнее",
                    url=mc["link"]
                )
            ],
        ]
    )

    text = (
        f"<b>{mc['title']}</b>\n"
        f"📍 {mc['place']}\n\n"
        f"{mc['description']}\n\n"
        f"👩‍🏫 Педагог: {mc['teacher']}\n"
        f"📅 {mc['date']}\n\n"
        f"💰 {mc['price']}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )

    await callback.answer()


# ===== Запись =====
@router.callback_query(lambda c: c.data == "mc_signup")
async def signup_master(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MasterForm.name)
    await callback.message.answer(
        "Введите ваше имя:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()


@router.message(MasterForm.name)
async def master_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(MasterForm.phone)
    await message.answer("Введите телефон для связи:")


@router.message(MasterForm.phone)
async def master_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mc = data["selected_mc"]
    name = data["name"]
    phone = message.text.strip()

    username_link = (
        f'<a href="https://t.me/{message.from_user.username}">@{message.from_user.username}</a>'
        if message.from_user.username
        else "без username"
    )

    # === Сообщение админу ===
    await message.bot.send_message(
        ADMIN_ID,
        f"🎨 <b>Новая запись на мастер-класс</b>\n\n"
        f"<b>Мероприятие:</b> {mc['title']}\n"
        f"<b>Дата:</b> {mc['date']}\n"
        f"<b>Стоимость:</b> {mc['price']}\n\n"
        f"<b>Клиент:</b> {name}\n"
        f"<b>Телефон:</b> {phone}\n"
        f"<b>Профиль:</b> {username_link}\n"
        f"<b>TG ID:</b> {message.from_user.id}",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    # === Клиенту ===
    await message.answer(
        f"✅ <b>Вы записаны!</b>\n\n"
        f"<b>{mc['title']}</b>\n"
        f"{mc['date']}\n\n"
        f"С вами скоро свяжется администратор для подтверждения.",
        parse_mode="HTML",
        reply_markup=bottom_kb(),
    )

    await state.clear()
