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
    selected_modules = State()
    num_people = State()
    name = State()
    phone = State()
    date = State()
    confirm = State()


# ─── ВЫБОР МОДУЛЕЙ ───────────────────────────────────────────────────────────

@dp.callback_query(lambda c: c.data == "main_package")
async def start_package(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(PackageForm.selected_modules)
    await state.update_data(selected_modules=[])

    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for module in PACKAGE_MODULES:
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=module, callback_data=f"pkg_mod_{module}")
        ])

    kb.inline_keyboard.append([
        InlineKeyboardButton(text="✅ Готово", callback_data="pkg_done")
    ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_main")
    ])

    await callback.message.edit_text(
        "Выберите модули для пакетного тура (максимум 3):",
        reply_markup=kb
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("pkg_mod_"))
async def toggle_package_module(callback: types.CallbackQuery, state: FSMContext):
    module = callback.data.replace("pkg_mod_", "")

    data = await state.get_data()
    selected = data.get("selected_modules", [])

    if module in selected:
        selected.remove(module)
    else:
        if len(selected) >= 3:
            await callback.answer("Можно выбрать максимум 3 модуля", show_alert=True)
            return
        selected.append(module)

    await state.update_data(selected_modules=selected)

    text = (
        f"Выбрано: {', '.join(selected) if selected else 'ничего'}\n\n"
        "Выберите модули (максимум 3):"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for mod in PACKAGE_MODULES:
        prefix = "✅ " if mod in selected else ""
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=prefix + mod, callback_data=f"pkg_mod_{mod}")
        ])

    kb.inline_keyboard.append([
        InlineKeyboardButton(text="✅ Готово", callback_data="pkg_done")
    ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="Отмена", callback_data="back_to_main")
    ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@dp.callback_query(lambda c: c.data == "pkg_done")
async def package_done(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_modules", [])

    if not selected:
        await callback.answer("Выберите хотя бы один модуль", show_alert=True)
        return

    await callback.message.edit_text("Укажите количество человек:")
    await state.set_state(PackageForm.num_people)
    await callback.answer()


# ─── КОЛИЧЕСТВО ЧЕЛОВЕК ──────────────────────────────────────────────────────

@dp.message(PackageForm.num_people)
async def process_num_people(message: types.Message, state: FSMContext):
    try:
        num = int(message.text.strip())
        if num <= 0 or num > 100:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректное число (например: 10)")
        return

    await state.update_data(num_people=num)
    await message.answer("Введите ваше имя:")
    await state.set_state(PackageForm.name)


# ─── ИМЯ ──────────────────────────────────────────────────────────────────────

@dp.message(PackageForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Введите номер телефона:")
    await state.set_state(PackageForm.phone)


# ─── ТЕЛЕФОН ──────────────────────────────────────────────────────────────────

@dp.message(PackageForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()

    if not re.fullmatch(r"\+?\d{10,15}", phone):
        await message.answer("Введите корректный номер телефона (только цифры, можно с +)")
        return

    await state.update_data(phone=phone)
    await message.answer("Введите желаемую дату (например: 25.03.2026):")
    await state.set_state(PackageForm.date)


# ─── ДАТА + РАСЧЁТ СТОИМОСТИ ─────────────────────────────────────────────────

@dp.message(PackageForm.date)
async def process_date(message: types.Message, state: FSMContext):
    date = message.text.strip()
    await state.update_data(date=date)

    data = await state.get_data()
    selected = data["selected_modules"]
    num_people = data["num_people"]

    modules_count = len(selected)
    total_per_person = 0

    for module in selected:
        prices = PACKAGE_MODULES[module]["prices"]
        price = prices[modules_count - 1]
        total_per_person += price

    total_sum = total_per_person * num_people

    await state.update_data(
        total_per_person=total_per_person,
        total_sum=total_sum
    )

    confirm_text = (
        "✨ <b>Проверьте данные заявки:</b>\n\n"
        f"📦 Модули: {', '.join(selected)}\n"
        f"👥 Количество человек: {num_people}\n"
        f"💰 Стоимость на 1 человека: {total_per_person} ₽\n"
        f"💳 Общая сумма: <b>{total_sum} ₽</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📅 Дата: {date}\n\n"
        "Подтвердить заявку?"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="pkg_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_main")]
    ])

    await message.answer(confirm_text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(PackageForm.confirm)


# ─── ПОДТВЕРЖДЕНИЕ ───────────────────────────────────────────────────────────

@dp.callback_query(lambda c: c.data == "pkg_confirm")
async def confirm_package(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    admin_text = (
        "📦 <b>Новая заявка на пакетный тур</b>\n\n"
        f"Модули: {', '.join(data['selected_modules'])}\n"
        f"Количество человек: {data['num_people']}\n"
        f"Стоимость на человека: {data['total_per_person']} ₽\n"
        f"Общая сумма: {data['total_sum']} ₽\n\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Дата: {data['date']}"
    )

    await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")

    await callback.message.edit_text(
        "✅ <b>Заявка успешно отправлена!</b>\n\n"
        "Наш администратор свяжется с вами в ближайшее время.",
        parse_mode="HTML",
        reply_markup=get_main_inline_keyboard()
    )

    await state.clear()
    await callback.answer()
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
    direction = State()
    current_list = State()  # сохраняем текущий список кружков

def parse_age_range(age_str):
    if not age_str or not isinstance(age_str, str):
        return None, None
    
    age_str = age_str.strip().lower()
    
    if "18+" in age_str or "18 +" in age_str:
        return 18, 999
    
    if '-' in age_str:
        parts = age_str.split('-')
        if len(parts) == 2:
            try:
                min_a = int(parts[0].strip())
                max_a = int(parts[1].strip())
                return min_a, max_a
            except ValueError:
                pass
    
    match = re.search(r'\d+', age_str)
    if match:
        try:
            min_a = int(match.group(0))
            return min_a, 999
        except ValueError:
            pass
    
    return None, None

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
        if dir_name:
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

# ─── ПАКЕТНЫЕ ТУРЫ ───────────────────────────────────────────────────────────
@dp.callback_query(lambda c: c.data == "main_package")
async def start_package(callback: types.CallbackQuery, state: FSMContext):
    logging.info("Открыта ветка Пакетные туры")
    await state.set_state(PackageForm.selected_modules)
    await state.update_data(selected_modules=[])
    
    text = "Выберите модули для пакетного тура (максимум 3):\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    
    for module in PACKAGE_MODULES:
        kb.inline_keyboard.append([InlineKeyboardButton(text=module, callback_data=f"pkg_mod_{module}")])
    
    kb.inline_keyboard.append([InlineKeyboardButton(text="✅ Готово", callback_data="pkg_done")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
    
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("pkg_mod_"))
async def toggle_package_module(callback: types.CallbackQuery, state: FSMContext):
    module = callback.data.replace("pkg_mod_", "")
    
    data = await state.get_data()
    selected = data.get("selected_modules", [])
    
    if module in selected:
        selected.remove(module)
    else:
        if len(selected) >= 3:
            await callback.answer("Максимум 3 модуля!", show_alert=True)
            return
        selected.append(module)
    
    await state.update_data(selected_modules=selected)
    
    # Обновляем сообщение с галочками
    text = f"Выбрано: {', '.join(selected) if selected else 'ничего'}\n\n" \
           f"Выберите модули для пакетного тура (максимум 3):"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for mod in PACKAGE_MODULES:
        prefix = "✅ " if mod in selected else ""
        kb.inline_keyboard.append([InlineKeyboardButton(text=prefix + mod, callback_data=f"pkg_mod_{mod}")])
    
    kb.inline_keyboard.append([InlineKeyboardButton(text="✅ Готово", callback_data="pkg_done")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
    
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "pkg_done")
async def package_done(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_modules", [])
    
    if not selected:
        await callback.answer("Выберите хотя бы один модуль!", show_alert=True)
        return
    
    await state.update_data(selected_modules=selected)
    await callback.message.edit_text(
        f"Вы выбрали: {', '.join(selected)}\n\n"
        "Укажите количество человек:"
    )
    await state.set_state(PackageForm.num_people)
    await callback.answer()

# ─── МАСТЕР-КЛАССЫ ───────────────────────────────────────────────────────────
@dp.callback_query(lambda c: c.data == "main_masterclass")
async def start_masterclass(callback: types.CallbackQuery, state: FSMContext):
    logging.info("Открыта ветка Мастер-классы")
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for addr in MASTERCLASSES:
        count = len(MASTERCLASSES[addr])
        text = f"{addr} ({count})" if count > 0 else addr
        kb.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"mclass_addr_{addr}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
    await callback.message.edit_text("Выберите адрес мастер-класса:", reply_markup=kb)
    await callback.answer()

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
            f"По адресу «{addr_key}» пока нет кружков."
        )
        await callback.answer()
        return

    await state.update_data(available_clubs=filtered)
    await callback.message.edit_text(
        "Укажите возраст (сколько полных лет ребёнку)?\n\n"
        "Просто введите число, например: 8"
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
        min_age, max_age = parse_age_range(age_str)
        
        if min_age is None or max_age is None:
            filtered_by_age.append(club)
            continue
        
        if min_age <= age <= max_age:
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
        await callback.message.edit_text("Ошибка выбора направления.")
        await callback.answer()
        return

    data = await state.get_data()
    filtered_by_age = data.get("filtered_by_age", [])

    directions = sorted(set(
        club.get("Наименование третьего уровня РБНДО", "Без направления").strip()
        for club in filtered_by_age
    ))

    if dir_idx >= len(directions):
        await callback.message.edit_text("Направление не найдено.")
        await callback.answer()
        return

    selected_dir = directions[dir_idx]
    await state.update_data(selected_dir=selected_dir)

    final_clubs = [
        club for club in filtered_by_age
        if club.get("Наименование третьего уровня РБНДО", "").strip() == selected_dir
    ]

    if not final_clubs:
        await callback.message.edit_text("По этому направлению нет кружков.")
    else:
        await state.update_data(current_list=final_clubs)
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
        await callback.message.edit_text("Ошибка выбора.")
        await callback.answer()
        return

    data = await state.get_data()
    clubs = data.get("current_list", [])
    if idx >= len(clubs):
        await callback.message.edit_text("Кружок не найден.")
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

