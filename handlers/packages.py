from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import ADMIN_ID
from keyboards import bottom_kb

router = Router()

PACKAGE_MODULES = {
    "Картинг": [2200, 2100, 2000],
    "Симрейсинг": [1600, 1500, 1400],
    "Практическая стрельба": [1600, 1500, 1400],
    "Лазертаг": [1600, 1500, 1400],
    "Керамика": [1600, 1500, 1400],
    "Мягкая игрушка": [1300, 1200, 1100],
}


class PackageForm(StatesGroup):
    people = State()
    activities = State()
    name = State()
    phone = State()


def activities_keyboard(selected=None):
    selected = selected or []
    builder = ReplyKeyboardBuilder()

    for name in PACKAGE_MODULES:
        text = f"{'✅ ' if name in selected else ''}{name}"
        builder.button(text=text)

    builder.button(text="🟢 Готово")
    builder.adjust(2, 1)

    return builder.as_markup(resize_keyboard=True)


@router.callback_query(lambda c: c.data == "m_package")
async def start_package(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PackageForm.people)
    await callback.message.answer(
        "Введите количество человек (минимум 5)."
    )
    await callback.answer()
