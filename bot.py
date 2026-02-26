import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения!")

ADMIN_ID = os.getenv('ADMIN_ID')
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не задан в переменных окружения!")
try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError(f"ADMIN_ID ('{ADMIN_ID}') не является корректным числом!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Машина состояний
class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()

# Хэндлер для /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот на aiogram 3.x. \n"
        "Напишите /form, чтобы заполнить анкету."
    )

# Хэндлер для команды /form
@dp.message(Command("form"))
async def cmd_form(message: types.Message, state: FSMContext):
    await state.set_state(Form.waiting_for_name)
    await message.answer("Введите ваше имя:")

# Хэндлер для ввода имени
@dp.message()
async def process_name(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Form.waiting_for_name.state:
        name = message.text
        await state.update_data(name=name)
        await state.set_state(Form.waiting_for_age)
        await message.answer("Теперь введите ваш возраст:")

# Хэндлер для ввода возраста
@dp.message()
async def process_age(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Form.waiting_for_age.state:
        age = message.text
        user_data = await state.get_data()
        name = user_data['name']
        await message.answer(f"Спасибо! Ваши данные: имя — {name}, возраст — {age}.")
        await state.clear()  # Очищаем состояние

# Хэндлер для любых других текстовых сообщений
@dp.message()
async def echo(message: types.Message):
    current_state = await state.get_state()
    # Если нет активного состояния — отвечаем эхом
    if not current_state:
        await message.answer(f"Вы написали: {message.text}")

# Основная функция запуска
async def main():
    logging.info("Бот запущен и начинает опрос обновлений...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
