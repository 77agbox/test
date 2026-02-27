import asyncio
import logging
import pandas as pd
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

# ===================== НАСТРОЙКИ =====================

BOT_TOKEN = "ВАШ_ТОКЕН"
ADMIN_ID = 462740408

logging.basicConfig(level=logging.INFO)

bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ===================== ДАННЫЕ =====================

clubs_df = pd.read_excel("joined_clubs.xlsx")

MASTER_CLASSES = {}  # {id: {...}}

PACKAGE_MODULES = {
    "Картинг": [2200, 2100, 2000],
    "Симрейсинг": [1600, 1500, 1400],
    "Практическая стрельба": [1600, 1500, 1400],
    "Лазертаг": [1600, 1500, 1400],
    "Керамика": [1600, 1500, 1400],
    "Мягкая игрушка": [1300, 1200, 1100],
}

# ===================== КЛАВИАТУРЫ =====================

def main_menu(user_id):
    buttons = [
        [InlineKeyboardButton(text="🎨 Кружки", callback_data="clubs")],
        [InlineKeyboardButton(text="🧑‍🏫 Мастер-классы", callback_data="master")],
        [InlineKeyboardButton(text="🎉 Пакетные туры", callback_data="package")],
        [InlineKeyboardButton(text="📝 Написать в поддержку", callback_data="support")],
    ]

    if user_id == ADMIN_ID:
        buttons.append(
            [InlineKeyboardButton(text="⚙ Админ панель", callback_data="admin")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_btn(where="menu"):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Назад", callback_data=where)]
        ]
    )


# ===================== START =====================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 <b>Бот Виктор</b>\n\n"
        "Я помогу выбрать занятия в центре «Виктория».\n\n"
        "Выберите раздел:",
        reply_markup=main_menu(message.from_user.id),
    )


@dp.callback_query(F.data == "menu")
async def back_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu(callback.from_user.id),
    )


# ===================== ПОДДЕРЖКА =====================

class SupportForm(StatesGroup):
    text = State()


@dp.callback_query(F.data == "support")
async def support_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportForm.text)
    await callback.message.answer("Напишите сообщение для поддержки:")


@dp.message(SupportForm.text)
async def support_send(message: Message, state: FSMContext):
    await bot.send_message(
        ADMIN_ID,
        f"📩 <b>Сообщение в поддержку</b>\n\n"
        f"👤 {message.from_user.full_name}\n"
        f"🆔 TG ID: {message.from_user.id}\n\n"
        f"{message.text}",
    )

    await message.answer("✅ Сообщение отправлено.", reply_markup=main_menu(message.from_user.id))
    await state.clear()


# ===================== КРУЖКИ =====================

class ClubsForm(StatesGroup):
    age = State()
    address = State()
    direction = State()


@dp.callback_query(F.data == "clubs")
async def clubs_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ClubsForm.age)
    await callback.message.answer("Введите возраст ребёнка (число):")


@dp.message(ClubsForm.age)
async def clubs_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число.")
        return

    age = int(message.text)
    filtered = clubs_df[clubs_df["Возраст"] == age]

    if filtered.empty:
        await message.answer("Нет кружков для этого возраста.")
        return

    await state.update_data(age=age)

    addresses = filtered["Адрес предоставления услуги"].fillna("ОНЛАЙН").unique()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=a, callback_data=f"addr_{a}")]
            for a in addresses
        ]
    )

    await state.set_state(ClubsForm.address)
    await message.answer("Выберите адрес:", reply_markup=kb)


@dp.callback_query(F.data.startswith("addr_"))
async def clubs_address(callback: CallbackQuery, state: FSMContext):
    addr = callback.data.replace("addr_", "")
    data = await state.get_data()
    age = data["age"]

    filtered = clubs_df[
        (clubs_df["Возраст"] == age)
        & (
            clubs_df["Адрес предоставления услуги"].fillna("ОНЛАЙН")
            == addr
        )
    ]

    directions = filtered["Наименование третьего уровня РБНДО"].unique()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=d, callback_data=f"dir_{d}")]
            for d in directions
        ]
    )

    await state.update_data(address=addr)
    await state.set_state(ClubsForm.direction)

    await callback.message.edit_text("Выберите направление:", reply_markup=kb)


@dp.callback_query(F.data.startswith("dir_"))
async def clubs_direction(callback: CallbackQuery, state: FSMContext):
    direction = callback.data.replace("dir_", "")
    data = await state.get_data()

    filtered = clubs_df[
        (clubs_df["Возраст"] == data["age"])
        & (clubs_df["Адрес предоставления услуги"].fillna("ОНЛАЙН") == data["address"])
        & (clubs_df["Наименование третьего уровня РБНДО"] == direction)
    ]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=row["Наименование детского объединения"],
                    callback_data=f"club_{index}",
                )
            ]
            for index, row in filtered.iterrows()
        ]
    )

    await callback.message.edit_text("Выберите кружок:", reply_markup=kb)


@dp.callback_query(F.data.startswith("club_"))
async def club_card(callback: CallbackQuery):
    idx = int(callback.data.replace("club_", ""))
    row = clubs_df.loc[idx]

    text = (
        f"<b>{row['Наименование детского объединения']}</b>\n\n"
        f"👶 Возраст: {row['Возраст']}\n"
        f"👩‍🏫 Педагог: {row['Педагог']}\n"
        f"📍 Адрес: {row['Адрес предоставления услуги']}\n"
        f"🔗 <a href='{row['Ссылка']}'>Подробнее</a>"
    )

    await callback.message.edit_text(text, reply_markup=back_btn("menu"))


# ===================== МАСТЕР-КЛАССЫ =====================

@dp.callback_query(F.data == "master")
async def show_master(callback: CallbackQuery):
    if not MASTER_CLASSES:
        await callback.message.answer("Пока нет мастер-классов.")
        return

    for mc in MASTER_CLASSES.values():
        text = (
            f"<b>{mc['name']}</b>\n\n"
            f"📅 {mc['date']}\n"
            f"💰 {mc['price']} ₽\n"
            f"👩‍🏫 {mc['teacher']}\n"
            f"{mc['desc']}"
        )
        await callback.message.answer(text)


# ===================== АДМИН =====================

@dp.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить МК", callback_data="add_mc")]
        ]
    )

    await callback.message.answer("Админ панель:", reply_markup=kb)


class AddMC(StatesGroup):
    name = State()
    date = State()
    price = State()
    teacher = State()
    desc = State()


@dp.callback_query(F.data == "add_mc")
async def add_mc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddMC.name)
    await callback.message.answer("Название мастер-класса:")


@dp.message(AddMC.name)
async def mc_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddMC.date)
    await message.answer("Дата и время:")


@dp.message(AddMC.date)
async def mc_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(AddMC.price)
    await message.answer("Стоимость:")


@dp.message(AddMC.price)
async def mc_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(AddMC.teacher)
    await message.answer("Педагог:")


@dp.message(AddMC.teacher)
async def mc_teacher(message: Message, state: FSMContext):
    await state.update_data(teacher=message.text)
    await state.set_state(AddMC.desc)
    await message.answer("Описание / ссылка:")


@dp.message(AddMC.desc)
async def mc_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    mc_id = len(MASTER_CLASSES) + 1
    data["desc"] = message.text
    MASTER_CLASSES[mc_id] = data

    await message.answer("✅ Мастер-класс добавлен.")
    await state.clear()


# ===================== ЗАПУСК =====================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
