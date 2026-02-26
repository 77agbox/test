import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('BOT_TOKEN'))
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
@dp.message(state=Form.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)
    await state.set_state(Form.waiting_for_age)
    await message.answer("Теперь введите ваш возраст:")

# Хэндлер для ввода возраста
@dp.message(state=Form.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    age = message.text
    user_data = await state.get_data()
    name = user_data['name']
    await message.answer(f"Спасибо! Ваши данные: имя — {name}, возраст — {age}.")
    await state.clear()  # Очищаем состояние

# Хэндлер для любых текстовых сообщений
@dp.message()
async def echo(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")

# Основная функция
async def main():
    await executor.start_polling(dp, bot=bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
