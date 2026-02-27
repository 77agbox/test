import asyncio
import logging
import os
import re
from datetime import datetime

import openpyxl
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv

# ===================== НАСТРОЙКА =====================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===================== ЗАГРУЗКА КРУЖКОВ =====================

def parse_age_range(age_str):
    if not age_str:
        return None, None

    age_str = str(age_str).lower()

    if "18+" in age_str:
        return 18, 99

    if "-" in age_str:
        parts = age_str.split("-")
        try:
            return int(parts[0]), int(parts[1])
        except:
            return None, None

    match = re.search(r"\d+", age_str)
    if match:
        return int(match.group()), 99

    return None, None


def load_clubs(file="joined_clubs.xlsx"):
    if not os.path.exists(file):
        logging.warning("Файл кружков не найден")
        return []

    wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
    sheet = wb.active

    headers = [c.value for c in next(sheet.iter_rows(min_row=1, max_row=1))]

    data = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        record = {}
        for h, v in zip(headers, row):
            record[h] = str(v).strip() if v else ""
        data.append(record)

    logging.info(f"Загружено кружков: {len(data)}")
    return data


CLUBS_DATA = load_clubs()

# ===================== СОСТОЯНИЯ =====================

class ClubsForm(StatesGroup):
    address = State()
    age = State()
    direction = State()


class SupportForm(StatesGroup):
    message = State()

# ===================== КЛАВИАТУРЫ =====================

def bottom_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Начать заново")
    builder.button(text="Поддержка")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Кружки", callback_data="clubs")],
        ]
    )

# ===================== СТАРТ =====================

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Здравствуйте! Выберите раздел:",
        reply_markup=bottom_kb(),
    )
    await message.answer("Главное меню:", reply_markup=main_menu())

# ===================== НАЧАТЬ ЗАНОВО =====================

@dp.message(lambda m: m.text == "Начать заново")
async def restart(message: types.Message, state: FSMContext):
    await state.clear()
    await start(message)

# ===================== ПОДДЕРЖКА =====================

@dp.message(lambda m: m.text == "Поддержка")
async def support_start(message: types.Message, state: FSMContext):
    await state.set_state(SupportForm.message)
    await message.answer("Введите сообщение:", reply_markup=ReplyKeyboardRemove())


@dp.message(SupportForm.message)
async def support_send(message: types.Message, state: FSMContext):
    await bot.send_message(
        ADMIN_ID,
        f"Сообщение от {message.from_user.full_name}\n\n{message.text}",
    )
    await message.answer("Сообщение отправлено.", reply_markup=bottom_kb())
    await state.clear()

# ===================== КРУЖКИ =====================

@dp.callback_query(lambda c: c.data == "clubs")
async def clubs_start(callback: types.CallbackQuery, state: FSMContext):
    addresses = list(set(c["Адрес предоставления услуги"] for c in CLUBS_DATA))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for addr in addresses:
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=addr, callback_data=f"addr_{addr}")]
        )

    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text="Назад", callback_data="back_main")]
    )

    await state.set_state(ClubsForm.address)
    await callback.message.edit_text("Выберите адрес:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("addr_"))
async def select_address(callback: types.CallbackQuery, state: FSMContext):
    address = callback.data.replace("addr_", "")
    await state.update_data(address=address)

    await state.set_state(ClubsForm.age)
    await callback.message.edit_text("Введите возраст ребёнка:")
    await callback.answer()


@dp.message(ClubsForm.age)
async def select_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
    except:
        await message.answer("Введите число.")
        return

    data = await state.get_data()
    address = data["address"]

    filtered = []
    for club in CLUBS_DATA:
        if club["Адрес предоставления услуги"] != address:
            continue

        min_age, max_age = parse_age_range(club["Возраст"])
        if min_age is None or (min_age <= age <= max_age):
            filtered.append(club)

    if not filtered:
        await message.answer("Нет кружков для этого возраста.", reply_markup=bottom_kb())
        await state.clear()
        return

    await state.update_data(filtered=filtered)

    directions = sorted(set(c["Наименование третьего уровня РБНДО"] for c in filtered))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for i, d in enumerate(directions):
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=d, callback_data=f"dir_{i}")]
        )

    await state.set_state(ClubsForm.direction)
    await message.answer("Выберите направление:", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith("dir_"))
async def select_direction(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.replace("dir_", ""))

    data = await state.get_data()
    filtered = data["filtered"]

    directions = sorted(set(c["Наименование третьего уровня РБНДО"] for c in filtered))
    selected_dir = directions[index]

    final = [c for c in filtered if c["Наименование третьего уровня РБНДО"] == selected_dir]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for i, club in enumerate(final):
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(
                text=club["Наименование детского объединения"],
                callback_data=f"club_{i}"
            )]
        )

    await state.update_data(final=final)
    await callback.message.edit_text("Выберите кружок:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("club_"))
async def show_club(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.replace("club_", ""))

    data = await state.get_data()
    club = data["final"][index]

    text = (
        f"<b>{club['Наименование детского объединения']}</b>\n\n"
        f"Возраст: {club['Возраст']}\n"
        f"Адрес: {club['Адрес предоставления услуги']}\n"
        f"Педагог: {club.get('Педагог','—')}\n"
        f"\nПодробнее: {club.get('Ссылка','—')}"
    )

    await callback.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

# ===================== ЗАПУСК =====================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
