import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import openpyxl

# ──────────────────────────────────────────────
TOKEN = os.getenv("BOT_TOKEN", "8606369205:AAEc80Rdnvg8fuogozkrc3VtqbZg9zZjG1E")
ADMIN_ID = int(os.getenv("ADMIN_ID", "462740408"))  # @sergienkoalvl
# ──────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
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
    num_people = State()
    activities = State()
    name = State()
    phone = State()
    date = State()

# ─── МАСТЕР-КЛАССЫ ───────────────────────────────────────────────────────────
MASTERCLASSES = {
    "Газопровод д.4": [
        {"title": "Сумочка для телефона", "date": "04.03.2026", "time": "17:00", "price": 1500, "description_link": "https://t.me/dyutsvictory/3733"},
        {"title": "Сумочка для телефона", "date": "26.02.2026", "time": "17:00", "price": 1500, "description_link": "https://t.me/dyutsvictory/3733"},
        {"title": "Подсвечник Ангел", "date": "25.03.2026", "time": "17:00", "price": 1200, "description_link": "https://t.me/dyutsvictory/3769"},
    ],
    "СП Щербинка": [],
    "МХС Аннино": [],
    "СП Юный техник": [],
}

ADDRESSES = list(MASTERCLASSES.keys())

class MasterclassForm(StatesGroup):
    address = State()
    list_view = State()
    detail_view = State()
    name = State()
    phone = State()

# ─── КРУЖКИ ──────────────────────────────────────────────────────────────────
ADDRESS_MAP = {
    "СП Щербинка": "город Москва, город Щербинка, Пушкинская улица, дом 3А",
    "МХС Аннино": "город Москва, Варшавское шоссе, дом 145, строение 1",
    "Газопровод д.4": "город Москва, улица Газопровод, дом 4",
    "СП Юный техник": "город Москва, Нагатинская улица, дом 22, корпус 2",
}

ADDRESSES_CLUBS = list(ADDRESS_MAP.keys()) + ["Онлайн"]

class ClubsForm(StatesGroup):
    address = State()
    age = State()

def load_clubs_data(file_path="joined_clubs.xlsx"):
    if not os.path.exists(file_path):
        logging.warning(f"Файл {file_path} не найден. Ветка 'Кружки' будет пустой.")
        return []
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet = wb.active
        headers = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1)) if cell.value]
        data = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row or row[0] is None:
                continue
            record = {}
            for h, v in zip(headers, row):
                record[h] = v if v is not None else ""
            data.append(record)
        logging.info(f"Загружено {len(data)} записей из файла {file_path}")
        return data
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {file_path}: {e}")
        return []

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

def get_addresses_inline_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for addr in ADDRESSES:
        count = len(MASTERCLASSES.get(addr, []))
        text = f"{addr} ({count})" if count > 0 else addr
        kb.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"addr_{addr}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
    return kb

def get_activities_keyboard(selected=None):
    selected = selected or []
    builder = ReplyKeyboardBuilder()
    for module in PACKAGE_MODULES:
        text = f"{module} {'✅' if module in selected else ''}"
        builder.button(text=text)
    builder.button(text="Готово")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_masterclasses_inline_keyboard(mcs):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for mc in mcs:
        text = f"{mc['title']} — {mc['date']}"
        kb.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"mc_select_{mc['title']}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_addresses")])
    return kb

def get_mc_actions_inline_keyboard(title):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подробнее", callback_data=f"mc_detail_{title}")],
        [InlineKeyboardButton(text="Записаться", callback_data=f"mc_signup_{title}")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_mcs")],
    ])

def get_clubs_addresses_inline_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for addr in ADDRESSES_CLUBS:
        if addr == "Онлайн":
            clubs = [c for c in CLUBS_DATA if not c.get("Адрес предоставления услуги")]
        else:
            full = ADDRESS_MAP.get(addr)
            clubs = [c for c in CLUBS_DATA if c.get("Адрес предоставления услуги") == full]
        count = len(clubs)
        text = f"{addr} ({count})" if count > 0 else addr
        kb.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"club_addr_{addr}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
    return kb

def get_ages_inline_keyboard(available_ages):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for age_range in sorted(set(available_ages)):
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=age_range, callback_data=f"club_age_{age_range}")
        ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_clubs_addresses")
    ])
    return kb

def get_clubs_list_inline_keyboard(clubs):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for club in clubs:
        title = club.get("Наименование детского объединения", "Без названия")
        cb_part = title.replace(" ", "_")[:50]
        display_text = title[:55] + "…" if len(title) > 55 else title
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=display_text, callback_data=f"club_select_{cb_part}")
        ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_clubs_ages")
    ])
    return kb

# ─── ОБЩИЕ ХЕНДЛЕРЫ ──────────────────────────────────────────────────────────
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

@dp.message(StateFilter("support"))
async def forward_support(message: types.Message, state: FSMContext):
    await bot.send_message(
        ADMIN_ID,
        f"Сообщение от {message.from_user.full_name} (@{message.from_user.username or 'нет'}):\n\n{message.text}"
    )
    await message.answer("Сообщение отправлено. Спасибо!", reply_markup=bottom_kb)
    await state.clear()

# ─── ПАКЕТНЫЕ ТУРЫ (заглушка — допиши позже) ─────────────────────────────────
@dp.callback_query(lambda c: c.data == "main_package")
async def start_package(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PackageForm.num_people)
    await callback.message.answer("Сколько человек в вашей группе?", reply_markup=ReplyKeyboardRemove())
    await callback.answer()

# ─── МАСТЕР-КЛАССЫ (заглушка — допиши позже) ─────────────────────────────────
@dp.callback_query(lambda c: c.data == "main_masterclass")
async def start_masterclass(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MasterclassForm.address)
    await callback.message.answer("Выберите адрес:", reply_markup=get_addresses_inline_keyboard())
    await callback.answer()

# ─── КРУЖКИ ──────────────────────────────────────────────────────────────────
@dp.callback_query(lambda c: c.data == "main_clubs")
async def start_clubs(callback: types.CallbackQuery, state: FSMContext):
    if not CLUBS_DATA:
        await callback.message.edit_text("Сейчас нет доступных кружков. Попробуйте позже.")
        await callback.answer()
        return

    await state.set_state(ClubsForm.address)
    await callback.message.edit_text(
        "Выберите адрес проведения занятий:",
        reply_markup=get_clubs_addresses_inline_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("club_addr_"))
async def process_club_address(callback: types.CallbackQuery, state: FSMContext):
    addr_key = callback.data.replace("club_addr_", "")
    await state.update_data(club_address=addr_key)

    if addr_key == "Онлайн":
        filtered = [c for c in CLUBS_DATA if not c.get("Адрес предоставления услуги")]
    else:
        full_addr = ADDRESS_MAP.get(addr_key)
        filtered = [c for c in CLUBS_DATA if c.get("Адрес предоставления услуги") == full_addr]

    ages = [c.get("Возраст", "Не указан") for c in filtered if c.get("Возраст")]
    unique_ages = sorted(set(ages))

    if not unique_ages:
        await callback.message.edit_text(
            f"По адресу «{addr_key}» пока нет кружков.\n\n"
            "Попробуйте другой адрес или следите за обновлениями.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Назад в меню", callback_data="back_to_main")
            ]])
        )
        await state.clear()
    else:
        await state.update_data(available_clubs=filtered)
        await state.set_state(ClubsForm.age)
        await callback.message.edit_text(
            "Выберите возрастную категорию:",
            reply_markup=get_ages_inline_keyboard(unique_ages)
        )

    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("club_age_"))
async def process_club_age(callback: types.CallbackQuery, state: FSMContext):
    age_range = callback.data.replace("club_age_", "")
    await state.update_data(club_age=age_range)

    data = await state.get_data()
    all_clubs = data.get("available_clubs", [])
    filtered_clubs = [c for c in all_clubs if c.get("Возраст") == age_range]

    if not filtered_clubs:
        await callback.message.edit_text(
            f"По возрасту «{age_range}» на этом адресе кружков нет.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Назад к возрастам", callback_data="back_to_clubs_ages")
            ]])
        )
    else:
        await callback.message.edit_text(
            f"Найдено кружков: {len(filtered_clubs)}\n\nВыберите:",
            reply_markup=get_clubs_list_inline_keyboard(filtered_clubs)
        )

    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("club_select_"))
async def process_club_select(callback: types.CallbackQuery, state: FSMContext):
    title_part = callback.data.replace("club_select_", "")

    data = await state.get_data()
    clubs = data.get("available_clubs", [])
    age = data.get("club_age")

    matching = [
        c for c in clubs
        if c.get("Возраст") == age
        and title_part in (c.get("Наименование детского объединения", "").replace(" ", "_"))
    ]

    if not matching:
        await callback.message.edit_text(
            "Не удалось найти выбранный кружок.\nПопробуйте выбрать заново.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Назад к списку", callback_data="back_to_clubs_ages")
            ]])
        )
        await callback.answer()
        return

    club = matching[0]

    pedagog = club.get("Педагог") or "не указан"
    link = club.get("Ссылка") or "ссылка отсутствует"

    text = (
        f"<b>{club.get('Наименование детского объединения', '—')}</b>\n\n"
        f"Возраст: {club.get('Возраст', '—')}\n"
        f"Адрес: {club.get('Адрес предоставления услуги', 'Онлайн')}\n"
        f"Педагог: {pedagog}\n\n"
        f"Подробнее: {link}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад к списку кружков", callback_data="back_to_clubs_ages")],
        [InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_main")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=False)
    await callback.answer()

# ─── НАЗАД ───────────────────────────────────────────────────────────────────
@dp.callback_query(lambda c: c.data in [
    "back_to_main",
    "back_to_clubs_addresses",
    "back_to_clubs_ages"
])
async def clubs_back(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "back_to_main":
        await state.clear()
        await callback.message.edit_text(
            "Выберите раздел:",
            reply_markup=get_main_inline_keyboard()
        )

    elif data == "back_to_clubs_addresses":
        await state.set_state(ClubsForm.address)
        await callback.message.edit_text(
            "Выберите адрес:",
            reply_markup=get_clubs_addresses_inline_keyboard()
        )

    elif data == "back_to_clubs_ages":
        d = await state.get_data()
        clubs = d.get("available_clubs", [])
        ages = [c.get("Возраст", "Не указан") for c in clubs if c.get("Возраст")]
        unique_ages = sorted(set(ages))
        await callback.message.edit_text(
            "Выберите возрастную категорию:",
            reply_markup=get_ages_inline_keyboard(unique_ages)
        )

    await callback.answer()

# ─── ЗАПУСК ──────────────────────────────────────────────────────────────────
async def main():
    try:
        me = await bot.get_me()
        logging.info(f"Бот запущен как @{me.username}")
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logging.error(f"Ошибка при запуске: {e}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
