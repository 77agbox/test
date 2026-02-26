import asyncio
import logging
import os
from datetime import datetime
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
ADMIN_ID = int(os.getenv("ADMIN_ID", "462740408"))
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
    "scherbinka": "город Москва, город Щербинка, Пушкинская улица, дом 3А",
    "annino": "город Москва, Варшавское шоссе, дом 145, строение 1",
    "gazoprovod": "город Москва, улица Газопровод, дом 4",
    "molodoy_tekhnik": "город Москва, Нагатинская улица, дом 22, корпус 2",
}

DISPLAY_NAMES = {
    "scherbinka": "СП Щербинка",
    "annino": "МХС Аннино",
    "gazoprovod": "Газопровод д.4",
    "molodoy_tekhnik": "СП Юный техник",
    "online": "Онлайн",
}

ADDRESSES_CLUBS = ["scherbinka", "annino", "gazoprovod", "molodoy_tekhnik", "online"]

class ClubsForm(StatesGroup):
    address = State()
    age = State()

def load_clubs_data(file_path="joined_clubs.xlsx"):
    if not os.path.exists(file_path):
        logging.warning(f"Файл {file_path} не найден.")
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
                if h == "Возраст":
                    # Принудительно приводим к строке и очищаем
                    if isinstance(v, datetime):
                        logging.warning(f"В столбце 'Возраст' найдена дата: {v} — заменяем на пустую строку")
                        v = ""
                    elif v is not None:
                        v = str(v).strip()
                    else:
                        v = ""
                record[h] = v if v is not None else ""

            data.append(record)

        logging.info(f"Загружено {len(data)} записей")
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

def get_clubs_addresses_inline_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for key in ADDRESSES_CLUBS:
        if key == "online":
            clubs = [c for c in CLUBS_DATA if not c.get("Адрес предоставления услуги")]
        else:
            full = ADDRESS_MAP.get(key)
            clubs = [c for c in CLUBS_DATA if c.get("Адрес предоставления услуги") == full]
        count = len(clubs)
        text = f"{DISPLAY_NAMES[key]} ({count})" if count > 0 else DISPLAY_NAMES[key]
        kb.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"club_addr_{key}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
    return kb

def get_ages_inline_keyboard(available_ages):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    # Только строки — никаких дат
    safe_ages = [str(a).strip() for a in available_ages if a and str(a).strip()]
    for age_range in sorted(set(safe_ages)):
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

@dp.message(StateFilter("support"))
async def forward_support(message: types.Message, state: FSMContext):
    await bot.send_message(
        ADMIN_ID,
        f"Сообщение от {message.from_user.full_name} (@{message.from_user.username or 'нет'}):\n\n{message.text}"
    )
    await message.answer("Сообщение отправлено. Спасибо!", reply_markup=bottom_kb)
    await state.clear()

# ─── КРУЖКИ ──────────────────────────────────────────────────────────────────
@dp.callback_query(lambda c: c.data == "main_clubs")
async def start_clubs(callback: types.CallbackQuery, state: FSMContext):
    logging.info("Открыта ветка Кружки")
    if not CLUBS_DATA:
        await callback.message.edit_text("Сейчас нет доступных кружков.")
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
    logging.info(f"Нажат адрес: {callback.data}")
    short_key = callback.data.replace("club_addr_", "")
    addr_key = DISPLAY_NAMES.get(short_key, short_key)

    await state.update_data(club_address=short_key)

    if short_key == "online":
        filtered = [c for c in CLUBS_DATA if not c.get("Адрес предоставления услуги")]
    else:
        full_addr = ADDRESS_MAP.get(short_key)
        if not full_addr:
            await callback.message.edit_text(f"Адрес '{addr_key}' не найден.")
            await callback.answer()
            return
        filtered = [c for c in CLUBS_DATA if c.get("Адрес предоставления услуги") == full_addr]

    # Защита: только строки
    ages = []
    for c in filtered:
        age = c.get("Возраст")
        if age and isinstance(age, str) and age.strip():
            ages.append(age.strip())
        else:
            ages.append("Не указан")

    unique_ages = sorted(set(ages))

    if not unique_ages or unique_ages == ["Не указан"]:
        await callback.message.edit_text(
            f"По адресу «{addr_key}» пока нет кружков с указанным возрастом.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Назад", callback_data="back_to_main")
            ]])
        )
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
    logging.info(f"Выбран возраст: {callback.data}")
    age_range = callback.data.replace("club_age_", "")
    await state.update_data(club_age=age_range)

    data = await state.get_data()
    all_clubs = data.get("available_clubs", [])
    filtered_clubs = [c for c in all_clubs if str(c.get("Возраст", "")).strip() == age_range]

    if not filtered_clubs:
        await callback.message.edit_text(
            f"По возрасту «{age_range}» кружков нет.",
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
    logging.info(f"Выбран кружок: {callback.data}")
    title_part = callback.data.replace("club_select_", "")

    data = await state.get_data()
    clubs = data.get("available_clubs", [])
    age = data.get("club_age")

    matching = [
        c for c in clubs
        if str(c.get("Возраст", "")).strip() == age
        and title_part in str(c.get("Наименование детского объединения", "")).replace(" ", "_")
    ]

    if not matching:
        await callback.message.edit_text("Кружок не найден. Попробуйте выбрать заново.")
    else:
        club = matching[0]
        text = (
            f"<b>{club.get('Наименование детского объединения', '—')}</b>\n\n"
            f"Возраст: {club.get('Возраст', '—')}\n"
            f"Адрес: {club.get('Адрес предоставления услуги', 'Онлайн')}\n"
            f"Педагог: {club.get('Педагог', 'не указан')}\n\n"
            f"Подробнее: {club.get('Ссылка', 'ссылка отсутствует')}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_clubs_ages")],
            [InlineKeyboardButton(text="В меню", callback_data="back_to_main")]
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)

    await callback.answer()

@dp.callback_query(lambda c: c.data in ["back_to_main", "back_to_clubs_addresses", "back_to_clubs_ages"])
async def clubs_back(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Нажата кнопка назад: {callback.data}")
    if callback.data == "back_to_main":
        await state.clear()
        await callback.message.edit_text("Выберите раздел:", reply_markup=get_main_inline_keyboard())
    elif callback.data == "back_to_clubs_addresses":
        await state.set_state(ClubsForm.address)
        await callback.message.edit_text("Выберите адрес:", reply_markup=get_clubs_addresses_inline_keyboard())
    elif callback.data == "back_to_clubs_ages":
        d = await state.get_data()
        clubs = d.get("available_clubs", [])
        ages = [str(c.get("Возраст", "Не указан")).strip() for c in clubs if c.get("Возраст")]
        await callback.message.edit_text(
            "Выберите возраст:",
            reply_markup=get_ages_inline_keyboard(sorted(set(ages)))
        )
    await callback.answer()

# ─── ЗАПУСК ──────────────────────────────────────────────────────────────────
async def main():
    try:
        me = await bot.get_me()
        logging.info(f"Бот запущен как @{me.username}")
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logging.error(f"Ошибка запуска: {e}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
