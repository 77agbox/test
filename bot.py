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
    direction = State()

def parse_min_age(age_str):
    if not age_str or not isinstance(age_str, str):
        return None
    age_str = age_str.strip().lower()
    if "18+" in age_str or "18 +" in age_str:
        return 18
    match = re.search(r'\d+', age_str)
    if match:
        try:
            return int(match.group(0))
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

def get_direction_keyboard(filtered_clubs):
    directions = set()
    for club in filtered_clubs:
        dir_name = club.get("Наименование третьего уровня РБНДО", "Без направления")
        directions.add(dir_name.strip())

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for idx, d in enumerate(sorted(directions)):
        short_d = d[:40] + "…" if len(d) > 40 else d
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=short_d, callback_data=f"club_dir_{idx}")
        ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_clubs_addresses")
    ])
    return kb

def get_clubs_list_inline_keyboard(clubs):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for idx, club in enumerate(clubs):
        title = club.get("Наименование детского объединения", "Без названия")
        display_text = title[:40] + "…" if len(title) > 40 else title
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=display_text, callback_data=f"club_sel_{idx}")
        ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_directions")
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
            await callback.message.edit_text(f"Адрес '{addr_key}' не найден.", reply_markup=None)
            await callback.answer()
            return
        filtered = [c for c in CLUBS_DATA if c.get("Адрес предоставления услуги") == full_addr]

    if not filtered:
        await callback.message.edit_text(
            f"По адресу «{addr_key}» пока нет кружков.",
            reply_markup=None
        )
        await callback.answer()
        return

    await state.update_data(available_clubs=filtered)
    await callback.message.edit_text(
        "Укажите возраст (сколько полных лет ребёнку)?\n\n"
        "Просто введите число, например: 8",
        reply_markup=None
    )
    await state.set_state(ClubsForm.age)
    await callback.answer()

@dp.message(ClubsForm.age)
async def process_age(message: types.Message, state: FSMContext):
    text = message.text.strip()
    try:
        age = int(text)
        if age < 0 or age > 120:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите целое число (возраст). Например: 7")
        return

    await state.update_data(age=age)

    data = await state.get_data()
    all_clubs = data.get("available_clubs", [])

    filtered_by_age = []
    for club in all_clubs:
        age_str = club.get("Возраст", "").strip()
        if not age_str:
            filtered_by_age.append(club)  # без возраста — показываем
            continue

        # Парсим диапазон
        min_age = None
        max_age = None

        if "18+" in age_str:
            min_age = 18
            max_age = 999  # взрослые
        elif '-' in age_str:
            parts = age_str.split('-')
            if len(parts) == 2:
                try:
                    min_age = int(parts[0].strip())
                    max_age = int(parts[1].strip())
                except ValueError:
                    pass
        else:
            # одиночное число или "с X лет"
            match = re.search(r'\d+', age_str)
            if match:
                try:
                    min_age = int(match.group(0))
                    max_age = 999
                except ValueError:
                    pass

        # Проверяем, подходит ли возраст ребёнка
        if min_age is None or max_age is None:
            filtered_by_age.append(club)  # не удалось распарсить — показываем
        elif min_age <= age <= max_age:
            filtered_by_age.append(club)

    if not filtered_by_age:
        await message.answer(
            f"Для возраста {age} лет на этом адресе подходящих кружков нет.\n"
            "Попробуйте другой адрес или возраст.",
            reply_markup=get_bottom_keyboard()
        )
        await state.clear()
        return

    await state.update_data(filtered_by_age=filtered_by_age)
    await message.answer(
        "Выберите направление:",
        reply_markup=get_direction_keyboard(filtered_by_age)
    )
    await state.set_state(ClubsForm.direction)

@dp.callback_query(lambda c: c.data.startswith("club_dir_"))
async def process_direction(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Выбрано направление: {callback.data}")
    dir_idx_str = callback.data.replace("club_dir_", "")
    try:
        dir_idx = int(dir_idx_str)
    except ValueError:
        await callback.message.edit_text("Ошибка выбора направления.", reply_markup=None)
        await callback.answer()
        return

    data = await state.get_data()
    filtered_by_age = data.get("filtered_by_age", [])

    directions = sorted(set(
        club.get("Наименование третьего уровня РБНДО", "Без направления").strip()
        for club in filtered_by_age
    ))

    if dir_idx >= len(directions):
        await callback.message.edit_text("Направление не найдено.", reply_markup=None)
        await callback.answer()
        return

    selected_dir = directions[dir_idx]
    await state.update_data(selected_dir=selected_dir)

    final_clubs = [
        club for club in filtered_by_age
        if club.get("Наименование третьего уровня РБНДО", "").strip() == selected_dir
    ]

    if not final_clubs:
        await callback.message.edit_text("По этому направлению нет кружков.", reply_markup=None)
    else:
        await callback.message.edit_text(
            f"Найдено кружков по направлению '{selected_dir}': {len(final_clubs)}\n\nВыберите:",
            reply_markup=get_clubs_list_inline_keyboard(final_clubs)
        )

    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("club_sel_"))
async def process_club_select(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Выбран кружок: {callback.data}")
    idx_str = callback.data.replace("club_sel_", "")
    try:
        idx = int(idx_str)
    except ValueError:
        await callback.message.edit_text("Ошибка выбора.", reply_markup=None)
        await callback.answer()
        return

    data = await state.get_data()
    clubs = data.get("filtered_by_age", [])  # или уточнить по направлению
    if idx >= len(clubs):
        await callback.message.edit_text("Кружок не найден.", reply_markup=None)
        await callback.answer()
        return

    club = clubs[idx]
    text = (
        f"<b>{club.get('Наименование детского объединения', '—')}</b>\n\n"
        f"Направление: {club.get('Наименование третьего уровня РБНДО', '—')}\n"
        f"Возраст: {club.get('Возраст', '—')}\n"
        f"Адрес: {club.get('Адрес предоставления услуги', 'Онлайн')}\n"
        f"Педагог: {club.get('Педагог', 'не указан')}\n\n"
        f"Подробнее: {club.get('Ссылка', 'ссылка отсутствует')}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_directions")],
        [InlineKeyboardButton(text="В меню", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

@dp.callback_query(lambda c: c.data in ["back_to_main", "back_to_clubs_addresses", "back_to_directions"])
async def clubs_back(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Нажата кнопка назад: {callback.data}")
    if callback.data == "back_to_main":
        await state.clear()
        await callback.message.edit_text("Выберите раздел:", reply_markup=get_main_inline_keyboard())
    elif callback.data == "back_to_clubs_addresses":
        await state.set_state(ClubsForm.address)
        await callback.message.edit_text("Выберите адрес:", reply_markup=get_clubs_addresses_inline_keyboard())
    elif callback.data == "back_to_directions":
        d = await state.get_data()
        clubs = d.get("filtered_by_age", [])
        await callback.message.edit_text(
            "Выберите направление:",
            reply_markup=get_direction_keyboard(clubs)
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

