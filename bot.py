import asyncio
import logging
import os
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import openpyxl

# ──────────────────────────────────────────────
# ЧТЕНИЕ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (BOT_TOKEN и ADMIN_ID)
# ──────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения!")

ADMIN_ID = int(os.getenv("ADMIN_ID"))
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не задан в переменных окружения!")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

RESTART_TEXT = "Начать заново"

# ─── ПАКЕТНЫЕ ТУРЫ ───────────────────────────────────────────────────────────
PACKAGE_MODULES = {
    "Картинг": {"prices": [2200, 2100, 2000]},
    "Симрейсинг": {"prices": [1600, 1500, 1400]},
    "Практическая стрельба": {"prices": [1600, 1500, 1400]},
    "Лазертаг": {"prices": [1600, 1500, 1400]},
    "Керамика": {"prices": [1600, 1500, 1400]},
    "Мягкая игрушка": {"prices": [1300, 1200, 1100]},
}

class PackageForm(StatesGroup):
    selected_modules = State()
    num_people = State()
    name = State()
    phone = State()
    date = State()
    confirm = State()

# ─── МАСТЕР-КЛАССЫ ───────────────────────────────────────────────────────────
MASTERCLASSES = {
    "Газопровод д.4": [
        {
            "title": "Сумочка для телефона",
            "date": "04.03.2026",
            "time": "17:00",
            "price": 1500,
            "description_link": "https://t.me/dyutsvictory/3733"
        },
    ],
}

class MasterclassForm(StatesGroup):
    address = State()
    selected = State()
    name = State()
    phone = State()

# ─── КРУЖКИ ──────────────────────────────────────────────────────────────────
ADDRESS_MAP = {
    "scherbinka": "город Москва, город Щербинка, Пушкинская улица, дом 3А",
    "annino": "город Москва, Варшавское шоссе, дом 145, строение 1",
}

ADDRESSES_CLUBS = ["scherbinka", "annino", "gazoprovod", "molodoy_tekhnik", "online"]

class ClubsForm(StatesGroup):
    address = State()
    age = State()
    direction = State()
    current_list = State()

def load_clubs_data(file_path="joined_clubs.xlsx"):
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    sheet = wb.active
    headers = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1)) if cell.value]
    data = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not row or row is None:
            continue
        record = {}
        for h, v in zip(headers, row):
            record[h] = v if v is not None else ""
        data.append(record)
    return data

CLUBS_DATA = load_clubs_data()

# ─── КЛАВИАТУРЫ ──────────────────────────────────────────────────────────────
def get_bottom_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text=RESTART_TEXT)
    builder.button(text="Написать в поддержку")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

bottom_kb = get_bottom_keyboard()

def get_main_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Кружки", callback_data="main_clubs")],
        [InlineKeyboardButton(text="Пакетные туры", callback_data="main_package")],
        [InlineKeyboardButton(text="Мастер-классы", callback_data="main_masterclass")],
    ])

# ─── ХЕНДЛЕРЫ ────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Это бот Центра «Виктория».\n\n"
        "Здесь можно записаться на кружок, пакетный тур или мастер-класс.",
        reply_markup=bottom_kb
    )
    await message.answer("Выберите раздел:", reply_markup=get_main_inline_keyboard())

@dp.message(lambda m: m.text == RESTART_TEXT)
async def restart(message: types.Message, state: FSMContext):
    await state.clear()
    await cmd_start(message)

@dp.message(lambda m: m.text == "Написать в поддержку")
async def start_support(message: types.Message, state: FSMContext):
    await message.answer(
        "Напишите ваше сообщение — оно будет отправлено администратору.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state("support")

@dp.message()
async def forward_support(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == "support":
        await bot.send_message(
            ADMIN_ID,
            f"Сообщение от {message.from_user.full_name} (@{message.from_user.username or 'нет'}):\n\n{message.text}"
        )
        await message.answer("Сообщение отправлено. Спасибо!", reply_markup=bottom_kb)
        await state.clear()

# ─── ПАКЕТНЫЕ ТУРЫ (хендлер) ────────────────────────────────────────────────
@dp.callback_query(lambda c: c.data == "main_package")
async def start_package(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(PackageForm.selected_modules)
    await state.update_data(selected_modules=[])
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for module in PACKAGE_MODULES:
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=module, callback_data=f"pkg_mod_{module}")
        ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="✅ Готово", callback_data="pkg_done"),
        InlineKeyboardButton(text="Назад", callback_data="back_to_main")
    ])
    await callback.message.edit_text(
        "Выберите модули для пакетного тура (максимум 3):",
        reply_markup=kb
    )
    await callback.answer()

# ─── ЗАПУСК БОТА ──────────────────────────────────────────────────────────────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

