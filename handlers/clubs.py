from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data_loader import load_clubs

router = Router()

CLUBS_DATA = load_clubs()


# ================= КАРТА АДРЕСОВ =================
# Короткое имя → полный адрес из Excel

ADDRESS_MAP = {
    "Газопровод, д.4": "город Москва, улица Газопровод, дом 4",
    "МХС Аннино": "город Москва, Варшавское шоссе, дом 145, строение 1",
    "СП Щербинка": "город Москва, город Щербинка, Пушкинская улица, дом 3А",
    "СП Юный техник": "город Москва, Нагатинская улица, дом 22, корпус 2",
}


# ================= FSM =================

class ClubsForm(StatesGroup):
    address = State()
    age = State()
    direction = State()
    club = State()


# ================= ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ =================

def parse_age(age_str: str):
    if not age_str:
        return None, None

    age_str = age_str.lower()

    if "-" in age_str:
        try:
            a, b = age_str.split("-")
            return int(a.strip()), int(b.strip())
        except:
            return None, None

    import re
    match = re.search(r"\d+", age_str)
    if match:
        return int(match.group()), 99

    return None, None


# ================= СТАРТ КРУЖКОВ =================

@router.callback_query(lambda c: c.data == "m_clubs")
async def start_clubs(callback: types.CallbackQuery, state: FSMContext):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=short_name,
                    callback_data=f"a_{i}"
                )
            ]
            for i, short_name in enumerate(ADDRESS_MAP.keys())
        ]
    )

    await state.update_data(address_keys=list(ADDRESS_MAP.keys()))
    await state.set_state(ClubsForm.address)

    await callback.message.edit_text(
        "📍 Выберите структурное подразделение:",
        reply_markup=keyboard
    )
    await callback.answer()


# ================= ВЫБОР АДРЕСА =================

@router.callback_query(lambda c: c.data.startswith("a_"))
async def select_address(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])

    data = await state.get_data()
    short_names = data["address_keys"]

    short_name = short_names[index]
    full_address = ADDRESS_MAP[short_name]

    await state.update_data(
        selected_address=full_address,
        selected_short_name=short_name
    )

    await state.set_state(ClubsForm.age)

    await callback.message.edit_text(
        f"📍 {short_name}\n\nВведите возраст ребёнка:"
    )
    await callback.answer()


# ================= ВВОД ВОЗРАСТА =================

@router.message(ClubsForm.age)
async def select_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
    except:
        await message.answer("Введите возраст числом.")
        return

    data = await state.get_data()
    address = data["selected_address"]

    filtered = []

    for club in CLUBS_DATA:
        if club.get("Адрес предоставления услуги") != address:
            continue

        min_age, max_age = parse_age(club.get("Возраст", ""))

        if min_age is None or (min_age <= age <= max_age):
            filtered.append(club)

    if not filtered:
        await message.answer("Подходящих кружков не найдено.")
        await state.clear()
        return

    await state.update_data(filtered=filtered)

    directions = sorted(
        set(c.get("Наименование третьего уровня РБНДО", "") for c in filtered)
    )

    await state.update_data(directions=directions)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=d,
                    callback_data=f"d_{i}"
                )
            ]
            for i, d in enumerate(directions)
        ]
        + [
            [InlineKeyboardButton(text="⬅ Назад", callback_data="m_clubs")]
        ]
    )

    await state.set_state(ClubsForm.direction)

    await message.answer(
        "🎯 Выберите направление:",
        reply_markup=keyboard
    )


# ================= ВЫБОР НАПРАВЛЕНИЯ =================

@router.callback_query(lambda c: c.data.startswith("d_"))
async def select_direction(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])

    data = await state.get_data()
    direction = data["directions"][index]

    clubs = [
        c for c in data["filtered"]
        if c.get("Наименование третьего уровня РБНДО") == direction
    ]

    await state.update_data(final=clubs)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=c.get("Наименование детского объединения", "")[:60],
                    callback_data=f"c_{i}"
                )
            ]
            for i, c in enumerate(clubs)
        ]
        + [
            [InlineKeyboardButton(text="⬅ Назад", callback_data="m_clubs")]
        ]
    )

    await state.set_state(ClubsForm.club)

    await callback.message.edit_text(
        "Выберите кружок:",
        reply_markup=keyboard
    )
    await callback.answer()


# ================= КАРТОЧКА КРУЖКА =================

@router.callback_query(lambda c: c.data.startswith("c_"))
async def show_club(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])

    data = await state.get_data()
    club = data["final"][index]

    text = (
        f"<b>{club.get('Наименование детского объединения', '')}</b>\n\n"
        f"Возраст: {club.get('Возраст', '')}\n"
        f"Адрес: {club.get('Адрес предоставления услуги', '')}\n"
        f"Педагог: {club.get('Педагог', '')}\n\n"
        f"{club.get('Ссылка', '')}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ В меню", callback_data="back_main")]
        ]
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )

    await callback.answer()
