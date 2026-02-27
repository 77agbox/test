from aiogram import Router, types
from aiogram.filters import CommandStart
from keyboards import main_menu, bottom_kb

router = Router()


@router.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в Центр «Виктория»!",
        reply_markup=bottom_kb(),
    )
    await message.answer("Выберите раздел:", reply_markup=main_menu())


@router.message(lambda m: m.text == "Начать заново")
async def restart(message: types.Message, state):
    await state.clear()
    await start(message)
@router.message()
async def catch_all_messages(message: types.Message):
    print("Необработанное сообщение:", message.text)
