from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data_loader import load_clubs
from keyboards import bottom_kb

router = Router()

CLUBS_DATA = load_clubs()


# ===== FSM =====
class ClubsForm(StatesGroup):
    address = State()
    age = State()
    direction = State()
    club = State()


# ===== Вспомогательная функция =====
def parse_age(age_str):
    if not age_str:
        return None, None

    age_str = str(age_str).lower()

    if "-" in age_str:
        try:
            a, b = age_str.split("-")
            return int(a), int(b)
        except:
            return None, None

    import re
    match = re.search(r"\d+", age_str)
    if match:
        return int(match.group()), 99

    return None, None


# ===== Старт кружков =====
@router.callback_query(lambda c: c.data == "m_clubs")
async def start_clubs(callback: types.CallbackQuery, state: FSMContext):
    addresses = sorted(list(set(c["Адрес предоставления услуги"] for c in CLUBS_DATA)))

    await state.update_data(addresses=addresses)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=addr, callback_data=f"a_{i}")]
            for i, addr in enumerate(addresses)
        ]
    )

    await state.set_state(ClubsForm.address)
    await callback.message.edit_text("📍 Выберите адрес:", reply_markup=keyboard)
    await callback.answer()


# ===== Выбор адреса =====
@router.callback_query(lambda c: c.data.startswith("a_"))
async def select_address(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    data = await state.get_data()
    address = data["addresses"][index]

    await state.update_data(selected_address=address)
    await state.set_state(ClubsForm.age)

    await callback.message.edit_text("Введите возраст ребёнка:")
    await callback.answer()


# ===== Ввод возраста =====
@router.message(ClubsForm.age)
async def select_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
    except:
        await message.answer("Введите число.")
        return

    data = await state.get_data()
    address = data["selected_address"]

    filtered = []
    for club in CLUBS_DATA:
        if club["Адрес предоставления услуги"] != address:
            continue

        min_age, max_age = parse_age(club["Возраст"])
        if min_age is None or (min_age <= age <= max_age):
            filtered.append(club)

    if not filtered:
        await message.answer(
            "Подходящих кружков нет.",
            reply_markup=bottom_kb(),
        )
        await state.clear()
        return

    await state.update_data(filtered=filtered)

    directions = sorted(
        set(c["Наименование третьего уровня РБНДО"] for c in filtered)
    )

    await state.update_data(directions=directions)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=d, callback_data=f"d_{i}")]
            for i, d in enumerate(directions)
        ]
    )

    await state.set_state(ClubsForm.direction)
    await message.answer("🎯 Выберите направление:", reply_markup=keyboard)


# ===== Выбор направления =====
@router.callback_query(lambda c: c.data.startswith("d_"))
async def select_direction(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])

    data = await state.get_data()
    direction = data["directions"][index]

    clubs = [
        c for c in data["filtered"]
        if c["Наименование третьего уровня РБНДО"] == direction
    ]

    await state.update_data(final=clubs)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=c["Наименование детского объединения"][:50],
                    callback_data=f"c_{i}"
                )
            ]
            for i, c in enumerate(clubs)
        ]
    )

    await state.set_state(ClubsForm.club)
    await callback.message.edit_text("Выберите кружок:", reply_markup=keyboard)
    await callback.answer()


# ===== Карточка кружка =====
@router.callback_query(lambda c: c.data.startswith("c_"))
async def show_club(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    data = await state.get_data()
    club = data["final"][index]

    text = (
        f"<b>{club['Наименование детского объединения']}</b>\n\n"
        f"Возраст: {club['Возраст']}\n"
        f"Адрес: {club['Адрес предоставления услуги']}\n"
        f"Педагог: {club.get('Педагог', '—')}\n\n"
        f"{club.get('Ссылка', '')}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    await callback.answer()
