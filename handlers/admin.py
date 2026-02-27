from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from contextlib import closing
import sqlite3

from config import ADMIN_ID
from database import add_masterclass, get_masterclasses, delete_masterclass


router = Router()


# ================= FSM =================

class AdminForm(StatesGroup):
    title = State()
    place = State()
    description = State()
    teacher = State()
    date = State()
    price = State()
    link = State()


class EditMasterclassForm(StatesGroup):
    title = State()
    place = State()
    description = State()
    teacher = State()
    date = State()
    price = State()
    link = State()


# ================= ПРОВЕРКА АДМИНА =================

def is_admin(user_id: int):
    return user_id == ADMIN_ID


# ================= ОТКРЫТЬ ПАНЕЛЬ =================

@router.callback_query(lambda c: c.data == "admin_panel")
async def open_admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить мастер-класс", callback_data="admin_add")],
            [InlineKeyboardButton(text="➖ Удалить мастер-класс", callback_data="admin_delete")],
            [InlineKeyboardButton(text="✏ Редактировать мастер-класс", callback_data="admin_edit")],
            [InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")]
        ]
    )

    await callback.message.edit_text(
        "⚙ <b>Админ-панель</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await callback.answer()


# ================= ДОБАВЛЕНИЕ МК =================

@router.callback_query(lambda c: c.data == "admin_add")
async def admin_add_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(AdminForm.title)
    await callback.message.answer("Введите название мастер-класса:")
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
async def admin_description(message: types.Message, state: FSMContext):
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
    await message.answer("Ссылка (https://...):")


@router.message(AdminForm.link)
async def admin_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data["link"] = message.text

    # Сохраняем мастер-класс в базе
    add_masterclass(data)

    await message.answer("✅ Мастер-класс успешно добавлен.")
    await state.clear()


# ================= УДАЛЕНИЕ МК =================

@router.callback_query(lambda c: c.data == "admin_delete")
async def admin_delete(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    rows = get_masterclasses()

    if not rows:
        await callback.message.edit_text("Нет доступных мастер-классов для удаления.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=row[1],  # title
                    callback_data=f"del_{row[0]}"  # id
                )
            ]
            for row in rows
        ] + [
            [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_panel")]
        ]
    )

    await callback.message.edit_text(
        "Выберите мастер-класс для удаления:",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("del_"))
async def confirm_delete(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    mc_id = int(callback.data.split("_")[1])
    delete_masterclass(mc_id)

    await callback.message.edit_text(
        "❌ Мастер-класс удалён.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_panel")]
            ]
        )
    )

    await callback.answer()


# ================= РЕДАКТИРОВАНИЕ МК =================

@router.callback_query(lambda c: c.data == "admin_edit")
async def admin_edit_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    rows = get_masterclasses()

    if not rows:
        await callback.message.edit_text("Нет доступных мастер-классов для редактирования.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=row[1],  # title
                    callback_data=f"edit_{row[0]}"  # id
                )
            ]
            for row in rows
        ] + [
            [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_panel")]
        ]
    )

    await callback.message.edit_text(
        "Выберите мастер-класс для редактирования:",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("edit_"))
async def edit_masterclass(callback: types.CallbackQuery, state: FSMContext):
    mc_id = int(callback.data.split("_")[1])

    rows = get_masterclasses()
    mc = next((row for row in rows if row[0] == mc_id), None)

    if not mc:
        await callback.answer("Мастер-класс не найден.")
        return

    await state.update_data(mc_id=mc_id)

    await state.set_state(EditMasterclassForm.title)
    await callback.message.edit_text("Редактирование мастер-класса\nВведите новое название:")
    await callback.answer()


@router.message(EditMasterclassForm.title)
async def edit_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(EditMasterclassForm.place)
    await message.answer("Введите новое место проведения:")


@router.message(EditMasterclassForm.place)
async def edit_place(message: types.Message, state: FSMContext):
    await state.update_data(place=message.text)
    await state.set_state(EditMasterclassForm.description)
    await message.answer("Введите новое описание:")


@router.message(EditMasterclassForm.description)
async def edit_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(EditMasterclassForm.teacher)
    await message.answer("Введите имя преподавателя:")


@router.message(EditMasterclassForm.teacher)
async def edit_teacher(message: types.Message, state: FSMContext):
    await state.update_data(teacher=message.text)
    await state.set_state(EditMasterclassForm.date)
    await message.answer("Введите дату и время:")


@router.message(EditMasterclassForm.date)
async def edit_date(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(EditMasterclassForm.price)
    await message.answer("Введите новую стоимость:")


@router.message(EditMasterclassForm.price)
async def edit_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(EditMasterclassForm.link)
    await message.answer("Введите ссылку (https://...):")


@router.message(EditMasterclassForm.link)
async def edit_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mc_id = data["mc_id"]
    data["link"] = message.text

    # Обновляем мастер-класс в базе
    with closing(sqlite3.connect("masterclasses.db")) as conn:
        with conn:
            conn.execute("""
                UPDATE masterclasses SET
                title = ?, place = ?, description = ?, teacher = ?, date = ?, price = ?, link = ?
                WHERE id = ?
            """, (
                data["title"],
                data["place"],
                data["description"],
                data["teacher"],
                data["date"],
                data["price"],
                data["link"],
                mc_id
            ))

    await message.answer("✅ Мастер-класс успешно обновлён.")
    await state.clear()
