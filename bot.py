import asyncio
import logging
import os
import re
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
    min_age = State()

def parse_min_age(age_str):
    if not age_str or not isinstance(age_str, str):
        return None
    age_str = age_str.strip().lower()
    if "18+" in age_str or "18 +" in age_str:
        return 18
    match = re.search(r'(?:с\s+)?(\d+)', age_str)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    if '-' in age_str:
        try:
            return int(age_str.split('-')[0].strip())
        except ValueError:
            pass
    return None

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
                    if isinstance(v, datetime):
                        logging.warning(f"Дата в 'Возраст': {v} → заменено на ''")
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

def get_min_age_keyboard(filtered_clubs):
    min_ages = set()
    has_adult = False

    for club in filtered_clubs:
        age_str = club.get("Возраст", "")
        if not age_str:
            continue
        min_age = parse_min_age(age_str)
        if min_age is not None:
            min_ages.add(min_age)
        if "18" in str(age_str):
            has_adult = True

    if has_adult:
        min_ages.add(18)

    sorted_min = sorted(min_ages)

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for min_age in sorted_min:
        text = f"С {min_age} лет" if min_age < 18 else "18+"
        # Короткий и безопасный callback_data
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=text, callback_data=f"club_min_{min_age}")
        ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_clubs_addresses")
    ])
    return kb

def get_clubs_list_inline_keyboard(clubs):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for club in clubs:
        title = club.get("Наименование детского объединения", "Без названия")
        # Короткий и чистый callback_data
        cb_part = re.sub(r'[^a-zA-Z0-9_]', '_', title)[:50]
        display_text = title[:55] + "…" if len(title) > 55 else title
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=display_text, callback_data=f"club_sel_{cb_part}")
        ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_min_age")
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

    if not filtered:
        await callback.message.edit_text(
            f"По адресу «{addr_key}» пока нет кружков.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Назад", callback_data="back_to_main")
            ]])
        )
        await callback.answer()
        return

    await state.update_data(available_clubs=filtered)
    await callback.message.edit_text(
        "Выберите минимальный возраст ребёнка:",
        reply_markup=get_min_age_keyboard(filtered)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("club_min_"))
async def process_min_age(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Выбран минимальный возраст: {callback.data}")
    min_age_str = callback.data.replace("club_min_", "")
    try:
        min_age = int(min_age_str)
    except ValueError:
        min_age = 18

    await state.update_data(min_age=min_age)

    data = await state.get_data()
    all_clubs = data.get("available_clubs", [])

    filtered_clubs = []
    for club in all_clubs:
        age_str = club.get("Возраст", "")
        club_min = parse_min_age(age_str)
        if club_min is None or club_min <= min_age:
            filtered_clubs.append(club)

    if not filtered_clubs:
        await callback.message.edit_text(
            f"Для возраста от {min_age} лет подходящих кружков нет.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Назад к адресам", callback_data="back_to_clubs_addresses")
            ]])
        )
    else:
        await callback.message.edit_text(
            f"Найдено подходящих кружков: {len(filtered_clubs)}\n\nВыберите:",
            reply_markup=get_clubs_list_inline_keyboard(filtered_clubs)
        )

    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("club_sel_"))
async def process_club_select(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Выбран кружок: {callback.data}")
    title_part = callback.data.replace("club_sel_", "")

    data = await state.get_data()
    clubs = data.get("available_clubs", [])
    min_age = data.get("min_age", 0)

    matching = []
    for c in clubs:
        club_age_str = str(c.get("Возраст", ""))
        club_min = parse_min_age(club_age_str)
        if club_min is None or club_min <= min_age:
            clean_title = str(c.get("Наименование детского объединения", "")).replace(" ", "_")
            if title_part in clean_title:
                matching.append(c)

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
            [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_min_age")],
            [InlineKeyboardButton(text="В меню", callback_data="back_to_main")]
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)

    await callback.answer()

@dp.callback_query(lambda c: c.data in ["back_to_main", "back_to_clubs_addresses", "back_to_min_age"])
async def clubs_back(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Нажата кнопка назад: {callback.data}")
    if callback.data == "back_to_main":
        await state.clear()
        await callback.message.edit_text("Выберите раздел:", reply_markup=get_main_inline_keyboard())
    elif callback.data == "back_to_clubs_addresses":
        await state.set_state(ClubsForm.address)
        await callback.message.edit_text("Выберите адрес:", reply_markup=get_clubs_addresses_inline_keyboard())
    elif callback.data == "back_to_min_age":
        d = await state.get_data()
        clubs = d.get("available_clubs", [])
        await callback.message.edit_text(
            "Выберите минимальный возраст ребёнка:",
            reply_markup=get_min_age_keyboard(clubs)
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
