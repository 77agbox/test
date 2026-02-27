from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_ID
from database import add_masterclass, get_masterclasses, delete_masterclass

router = Router()


class AdminForm(StatesGroup):
    title = State()
    place = State()
    description = State()
    teacher = State()
    date = State()
    price = State()
    link = State()


# ===== Админ меню =====

@router.message(lambda m: m.text == "⚙ Админ-панель")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить мастер-класс", callback_data="admin_add")],
        [InlineKeyboardButton(text="➖ Удалить мастер-класс", callback_data="admin_delete")],
    ])

    await message.answer("Админ-панель:", reply_markup=keyboard)


# ===== Добавление =====

@router.callback_query(lambda c: c.data == "admin_add")
async def admin_add_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminForm.title)
    await callback.message.answer("Название мастер-класса:")
    await callback.answer()


@router.message(AdminForm.title)
async def admin_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdminForm.place)
    await message.answer("Место проведения:")


@router.message(AdminForm.place)
async def admin_place(message: types.Message, state: FSMContext):
    await state.update_data(place=message.text)
    await state.set_state(AdminForm.description)
    await message.answer("Описание:")


@router.message(AdminForm.description)
async def admin_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdminForm.teacher)
    await message.answer("Педагог:")


@router.message(AdminForm.teacher)
async def admin_teacher(message: types.Message, state: FSMContext):
    await state.update_data(teacher=message.text)
    await state.set_state(AdminForm.date)
    await message.answer("Дата и время:")


@router.message(AdminForm.date)
async def admin_date(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(AdminForm.price)
    await message.answer("Стоимость:")


@router.message(AdminForm.price)
async def admin_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(AdminForm.link)
    await message.answer("Ссылка (https://...)")


@router.message(AdminForm.link)
async def admin_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data["link"] = message.text

    add_masterclass(data)

    await message.answer("✅ Мастер-класс добавлен.")
    await state.clear()


# ===== Удаление =====

@router.callback_query(lambda c: c.data == "admin_delete")
async def admin_delete(callback: types.CallbackQuery):
    rows = get_masterclasses()

    if not rows:
        await callback.message.answer("Нет активных мастер-классов.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=row[1],
                    callback_data=f"del_{row[0]}"
                )
            ]
            for row in rows
        ]
    )

    await callback.message.answer("Выберите для удаления:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("del_"))
async def confirm_delete(callback: types.CallbackQuery):
    mc_id = int(callback.data.split("_")[1])
    delete_masterclass(mc_id)

    await callback.message.answer("❌ Мастер-класс удалён.")
    await callback.answer()
