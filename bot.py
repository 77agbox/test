 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/bot.py b/bot.py
index c4dbced8a1073a752136579f90c09053f1256182..bfadfeacd8b015017058fbd412f447848fa19f50 100644
--- a/bot.py
+++ b/bot.py
@@ -1,86 +1,828 @@
-import asyncio
-import os
-import logging
-from aiogram import Bot, Dispatcher, types
-from aiogram.filters import Command
-from aiogram.fsm.context import FSMContext
-from aiogram.fsm.state import State, StatesGroup
-from dotenv import load_dotenv
-
-# Загружаем переменные из .env
-load_dotenv()
-
-# Настройка логирования
-logging.basicConfig(level=logging.INFO)
-
-# Инициализация бота и диспетчера
-BOT_TOKEN = os.getenv('BOT_TOKEN')
-if not BOT_TOKEN:
-    raise ValueError("BOT_TOKEN не задан в переменных окружения!")
-
-ADMIN_ID = os.getenv('ADMIN_ID')
-if not ADMIN_ID:
-    raise ValueError("ADMIN_ID не задан в переменных окружения!")
-try:
-    ADMIN_ID = int(ADMIN_ID)
-except ValueError:
-    raise ValueError(f"ADMIN_ID ('{ADMIN_ID}') не является корректным числом!")
-
-bot = Bot(token=BOT_TOKEN)
-dp = Dispatcher()
-
-# Машина состояний
-class Form(StatesGroup):
-    waiting_for_name = State()
-    waiting_for_age = State()
-
-# Хэндлер для /start
-@dp.message(Command("start"))
-async def cmd_start(message: types.Message):
-    await message.answer(
-        "Привет! Я бот на aiogram 3.x. \n"
-        "Напишите /form, чтобы заполнить анкету."
-    )
-
-# Хэндлер для команды /form
-@dp.message(Command("form"))
-async def cmd_form(message: types.Message, state: FSMContext):
-    await state.set_state(Form.waiting_for_name)
-    await message.answer("Введите ваше имя:")
-
-# Хэндлер для ввода имени
-@dp.message()
-async def process_name(message: types.Message, state: FSMContext):
-    current_state = await state.get_state()
-    if current_state == Form.waiting_for_name.state:
-        name = message.text
-        await state.update_data(name=name)
-        await state.set_state(Form.waiting_for_age)
-        await message.answer("Теперь введите ваш возраст:")
-
-# Хэндлер для ввода возраста
-@dp.message()
-async def process_age(message: types.Message, state: FSMContext):
-    current_state = await state.get_state()
-    if current_state == Form.waiting_for_age.state:
-        age = message.text
-        user_data = await state.get_data()
-        name = user_data['name']
-        await message.answer(f"Спасибо! Ваши данные: имя — {name}, возраст — {age}.")
-        await state.clear()  # Очищаем состояние
-
-# Хэндлер для любых других текстовых сообщений
-@dp.message()
-async def echo(message: types.Message):
-    current_state = await state.get_state()
-    # Если нет активного состояния — отвечаем эхом
-    if not current_state:
-        await message.answer(f"Вы написали: {message.text}")
-
-# Основная функция запуска
-async def main():
-    logging.info("Бот запущен и начинает опрос обновлений...")
-    await dp.start_polling(bot)
-
-if __name__ == '__main__':
-    asyncio.run(main())
+import asyncio
+import logging
+import os
+import re
+from datetime import datetime
+
+import openpyxl
+from aiogram import Bot, Dispatcher, types
+from aiogram.filters import CommandStart, StateFilter
+from aiogram.fsm.context import FSMContext
+from aiogram.fsm.state import State, StatesGroup
+from aiogram.fsm.storage.memory import MemoryStorage
+from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
+from aiogram.utils.keyboard import ReplyKeyboardBuilder
+from dotenv import load_dotenv
+
+load_dotenv()
+
+BOT_TOKEN = os.getenv("BOT_TOKEN")
+if not BOT_TOKEN:
+    raise ValueError("BOT_TOKEN не задан в переменных окружения")
+
+ADMIN_ID_RAW = os.getenv("ADMIN_ID")
+if not ADMIN_ID_RAW:
+    raise ValueError("ADMIN_ID не задан в переменных окружения")
+
+try:
+    ADMIN_ID = int(ADMIN_ID_RAW)
+except ValueError as exc:
+    raise ValueError(f"ADMIN_ID ('{ADMIN_ID_RAW}') не является корректным числом") from exc
+
+logging.basicConfig(level=logging.INFO)
+bot = Bot(token=BOT_TOKEN)
+storage = MemoryStorage()
+dp = Dispatcher(storage=storage)
+
+PACKAGE_MODULES = {
+    "Картинг": {"prices": [2200, 2100, 2000]},
+    "Симрейсинг": {"prices": [1600, 1500, 1400]},
+    "Практическая стрельба": {"prices": [1600, 1500, 1400]},
+    "Лазертаг": {"prices": [1600, 1500, 1400]},
+    "Керамика": {"prices": [1600, 1500, 1400]},
+    "Мягкая игрушка": {"prices": [1300, 1200, 1100]},
+}
+
+
+class PackageForm(StatesGroup):
+    num_people = State()
+    activities = State()
+    name = State()
+    phone = State()
+    date = State()
+
+
+MASTERCLASSES = {
+    "Газопровод д.4": [
+        {
+            "title": "Сумочка для телефона",
+            "date": "04.03.2026",
+            "time": "17:00",
+            "price": 1500,
+            "description_link": "https://t.me/dyutsvictory/3733",
+        },
+        {
+            "title": "Сумочка для телефона",
+            "date": "26.02.2026",
+            "time": "17:00",
+            "price": 1500,
+            "description_link": "https://t.me/dyutsvictory/3733",
+        },
+        {
+            "title": "Подсвечник Ангел",
+            "date": "25.03.2026",
+            "time": "17:00",
+            "price": 1200,
+            "description_link": "https://t.me/dyutsvictory/3769",
+        },
+    ],
+    "СП Щербинка": [],
+    "МХС Аннино": [],
+    "СП Юный техник": [],
+}
+
+ADDRESSES = list(MASTERCLASSES.keys())
+
+
+class MasterclassForm(StatesGroup):
+    address = State()
+    list_view = State()
+    detail_view = State()
+    name = State()
+    phone = State()
+
+
+ADDRESS_MAP = {
+    "scherbinka": "город Москва, город Щербинка, Пушкинская улица, дом 3А",
+    "annino": "город Москва, Варшавское шоссе, дом 145, строение 1",
+    "gazoprovod": "город Москва, улица Газопровод, дом 4",
+    "molodoy_tekhnik": "город Москва, Нагатинская улица, дом 22, корпус 2",
+}
+
+DISPLAY_NAMES = {
+    "scherbinka": "СП Щербинка",
+    "annino": "МХС Аннино",
+    "gazoprovod": "Газопровод д.4",
+    "molodoy_tekhnik": "СП Юный техник",
+    "online": "Онлайн",
+}
+
+ADDRESSES_CLUBS = ["scherbinka", "annino", "gazoprovod", "molodoy_tekhnik", "online"]
+
+
+class ClubsForm(StatesGroup):
+    address = State()
+    age = State()
+    direction = State()
+
+
+def parse_age_range(age_str):
+    if not age_str or not isinstance(age_str, str):
+        return None, None
+
+    age_str = age_str.strip().lower()
+
+    if "18+" in age_str or "18 +" in age_str:
+        return 18, 999
+
+    if "-" in age_str:
+        parts = age_str.split("-")
+        if len(parts) == 2:
+            try:
+                min_a = int(parts[0].strip())
+                max_a = int(parts[1].strip())
+                return min_a, max_a
+            except ValueError:
+                pass
+
+    match = re.search(r"\d+", age_str)
+    if match:
+        try:
+            min_a = int(match.group(0))
+            return min_a, 999
+        except ValueError:
+            pass
+
+    return None, None
+
+
+def load_clubs_data(file_path="joined_clubs.xlsx"):
+    if not os.path.exists(file_path):
+        logging.warning("Файл %s не найден.", file_path)
+        return []
+
+    try:
+        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
+        sheet = wb.active
+
+        headers = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1)) if cell.value]
+
+        data = []
+        for row in sheet.iter_rows(min_row=2, values_only=True):
+            if not row or row[0] is None:
+                continue
+
+            record = {}
+            for h, v in zip(headers, row):
+                if h == "Возраст":
+                    if isinstance(v, datetime):
+                        logging.warning("Дата в 'Возраст': %s → заменено на ''", v)
+                        v = ""
+                    elif v is not None:
+                        v = str(v).strip()
+                    else:
+                        v = ""
+                record[h] = v if v is not None else ""
+
+            data.append(record)
+
+        logging.info("Загружено %s записей кружков", len(data))
+        return data
+    except Exception as exc:
+        logging.error("Ошибка при чтении файла %s: %s", file_path, exc)
+        return []
+
+
+CLUBS_DATA = load_clubs_data()
+
+
+def get_bottom_keyboard():
+    builder = ReplyKeyboardBuilder()
+    builder.button(text="Начать заново")
+    builder.button(text="Написать в поддержку")
+    builder.adjust(2)
+    return builder.as_markup(resize_keyboard=True)
+
+
+bottom_kb = get_bottom_keyboard()
+
+
+def get_main_inline_keyboard():
+    return InlineKeyboardMarkup(
+        inline_keyboard=[
+            [InlineKeyboardButton(text="Кружки", callback_data="main_clubs")],
+            [InlineKeyboardButton(text="Пакетные туры", callback_data="main_package")],
+            [InlineKeyboardButton(text="Мастер-классы", callback_data="main_masterclass")],
+        ]
+    )
+
+
+def get_addresses_inline_keyboard():
+    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
+    for addr in ADDRESSES:
+        count = len(MASTERCLASSES.get(addr, []))
+        text = f"{addr} ({count})" if count > 0 else addr
+        keyboard.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"addr_{addr}")])
+    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
+    return keyboard
+
+
+def get_clubs_addresses_inline_keyboard():
+    kb = InlineKeyboardMarkup(inline_keyboard=[])
+    for key in ADDRESSES_CLUBS:
+        if key == "online":
+            clubs = [club for club in CLUBS_DATA if not club.get("Адрес предоставления услуги")]
+        else:
+            full = ADDRESS_MAP.get(key)
+            clubs = [
+                club for club in CLUBS_DATA if club.get("Адрес предоставления услуги") == full
+            ]
+        count = len(clubs)
+        text = f"{DISPLAY_NAMES[key]} ({count})" if count > 0 else DISPLAY_NAMES[key]
+        kb.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"club_addr_{key}")])
+    kb.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
+    return kb
+
+
+def get_direction_keyboard(filtered_clubs):
+    directions = set()
+    for club in filtered_clubs:
+        dir_name = club.get("Наименование третьего уровня РБНДО", "Без направления")
+        if dir_name:
+            directions.add(dir_name.strip())
+
+    kb = InlineKeyboardMarkup(inline_keyboard=[])
+    for idx, direction in enumerate(sorted(directions)):
+        short_name = direction[:40] + "…" if len(direction) > 40 else direction
+        kb.inline_keyboard.append(
+            [InlineKeyboardButton(text=short_name, callback_data=f"club_dir_{idx}")]
+        )
+    kb.inline_keyboard.append(
+        [InlineKeyboardButton(text="Назад", callback_data="back_to_clubs_addresses")]
+    )
+    return kb
+
+
+def get_clubs_list_inline_keyboard(clubs):
+    kb = InlineKeyboardMarkup(inline_keyboard=[])
+    for idx, club in enumerate(clubs):
+        title = club.get("Наименование детского объединения", "Без названия")
+        short_title = title[:50] + "…" if len(title) > 50 else title
+        kb.inline_keyboard.append(
+            [InlineKeyboardButton(text=short_title, callback_data=f"club_sel_{idx}")]
+        )
+    kb.inline_keyboard.append(
+        [InlineKeyboardButton(text="Назад", callback_data="back_to_directions")]
+    )
+    return kb
+
+
+def get_activities_keyboard(selected=None):
+    selected = selected or []
+    builder = ReplyKeyboardBuilder()
+    for module in PACKAGE_MODULES:
+        text = f"{module} {'✅' if module in selected else ''}".strip()
+        builder.button(text=text)
+    builder.button(text="Готово")
+    builder.adjust(2)
+    return builder.as_markup(resize_keyboard=True)
+
+
+def get_masterclasses_inline_keyboard(mcs):
+    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
+    for mc in mcs:
+        text = f"{mc['title']} — {mc['date']}"
+        keyboard.inline_keyboard.append(
+            [InlineKeyboardButton(text=text, callback_data=f"mc_select_{mc['title']}")]
+        )
+    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back_to_addresses")])
+    return keyboard
+
+
+def get_mc_actions_inline_keyboard(title):
+    return InlineKeyboardMarkup(
+        inline_keyboard=[
+            [InlineKeyboardButton(text="Подробнее", callback_data=f"mc_detail_{title}")],
+            [InlineKeyboardButton(text="Записаться", callback_data=f"mc_signup_{title}")],
+            [InlineKeyboardButton(text="Назад", callback_data="back_to_mcs")],
+        ]
+    )
+
+
+@dp.message(CommandStart())
+async def cmd_start(message: types.Message):
+    await message.answer(
+        "Здравствуйте, я бот Центра «Виктория».\n\n"
+        "Здесь можно подобрать кружок, пакетный тур или записаться на мастер-класс.",
+        reply_markup=bottom_kb,
+    )
+    await message.answer("Выберите действие:", reply_markup=get_main_inline_keyboard())
+
+
+@dp.message(lambda m: m.text == "Начать заново")
+async def restart(message: types.Message, state: FSMContext):
+    await state.clear()
+    await cmd_start(message)
+
+
+@dp.message(lambda m: m.text == "Написать в поддержку")
+async def start_support(message: types.Message, state: FSMContext):
+    await message.answer(
+        "Напишите ваше сообщение, и оно будет отправлено администратору.",
+        reply_markup=ReplyKeyboardRemove(),
+    )
+    await state.set_state("support_message")
+
+
+@dp.message(StateFilter("support_message"))
+async def forward_to_support(message: types.Message, state: FSMContext):
+    await bot.send_message(
+        ADMIN_ID,
+        f"Сообщение от {message.from_user.full_name} (@{message.from_user.username or 'нет'}):\n\n"
+        f"{message.text}",
+    )
+    await message.answer("Сообщение отправлено администратору. Спасибо!", reply_markup=bottom_kb)
+    await state.clear()
+
+
+@dp.callback_query(lambda c: c.data == "main_clubs")
+async def start_clubs(callback: types.CallbackQuery, state: FSMContext):
+    logging.info("Открыта ветка Кружки")
+    if not CLUBS_DATA:
+        await callback.message.edit_text("Сейчас нет доступных кружков.")
+        await callback.answer()
+        return
+
+    await state.set_state(ClubsForm.address)
+    await callback.message.edit_text(
+        "Выберите адрес проведения занятий:", reply_markup=get_clubs_addresses_inline_keyboard()
+    )
+    await callback.answer()
+
+
+@dp.callback_query(lambda c: c.data.startswith("club_addr_"))
+async def process_club_address(callback: types.CallbackQuery, state: FSMContext):
+    logging.info("Нажат адрес: %s", callback.data)
+    short_key = callback.data.replace("club_addr_", "")
+    addr_key = DISPLAY_NAMES.get(short_key, short_key)
+
+    await state.update_data(club_address=short_key)
+
+    if short_key == "online":
+        filtered = [club for club in CLUBS_DATA if not club.get("Адрес предоставления услуги")]
+    else:
+        full_addr = ADDRESS_MAP.get(short_key)
+        if not full_addr:
+            await callback.message.edit_text(f"Адрес '{addr_key}' не найден.")
+            await callback.answer()
+            return
+        filtered = [
+            club for club in CLUBS_DATA if club.get("Адрес предоставления услуги") == full_addr
+        ]
+
+    if not filtered:
+        await callback.message.edit_text(f"По адресу «{addr_key}» пока нет кружков.")
+        await callback.answer()
+        return
+
+    await state.update_data(available_clubs=filtered)
+    await callback.message.edit_text(
+        "Укажите возраст (сколько полных лет ребёнку)?\n\n"
+        "Просто введите число, например: 8"
+    )
+    await state.set_state(ClubsForm.age)
+    await callback.answer()
+
+
+@dp.message(ClubsForm.age)
+async def process_club_age(message: types.Message, state: FSMContext):
+    text = message.text.strip()
+    try:
+        age = int(text)
+        if age < 0 or age > 120:
+            raise ValueError
+    except ValueError:
+        await message.answer("Пожалуйста, введите целое число (возраст). Например: 7")
+        return
+
+    await state.update_data(age=age)
+
+    data = await state.get_data()
+    all_clubs = data.get("available_clubs", [])
+
+    filtered_by_age = []
+    for club in all_clubs:
+        age_str = club.get("Возраст", "").strip()
+        min_age, max_age = parse_age_range(age_str)
+
+        if min_age is None or max_age is None:
+            filtered_by_age.append(club)
+            continue
+
+        if min_age <= age <= max_age:
+            filtered_by_age.append(club)
+
+    if not filtered_by_age:
+        await message.answer(
+            f"Для возраста {age} лет на этом адресе подходящих кружков нет.\n"
+            "Попробуйте другой адрес или возраст.",
+            reply_markup=get_bottom_keyboard(),
+        )
+        await state.clear()
+        return
+
+    await state.update_data(filtered_by_age=filtered_by_age)
+    await message.answer(
+        "Выберите направление:",
+        reply_markup=get_direction_keyboard(filtered_by_age),
+    )
+    await state.set_state(ClubsForm.direction)
+
+
+@dp.callback_query(lambda c: c.data.startswith("club_dir_"))
+async def process_direction(callback: types.CallbackQuery, state: FSMContext):
+    logging.info("Выбрано направление: %s", callback.data)
+    dir_idx_str = callback.data.replace("club_dir_", "")
+    try:
+        dir_idx = int(dir_idx_str)
+    except ValueError:
+        await callback.message.edit_text("Ошибка выбора направления.")
+        await callback.answer()
+        return
+
+    data = await state.get_data()
+    filtered_by_age = data.get("filtered_by_age", [])
+
+    directions = sorted(
+        set(
+            club.get("Наименование третьего уровня РБНДО", "Без направления").strip()
+            for club in filtered_by_age
+        )
+    )
+
+    if dir_idx >= len(directions):
+        await callback.message.edit_text("Направление не найдено.")
+        await callback.answer()
+        return
+
+    selected_dir = directions[dir_idx]
+    await state.update_data(selected_dir=selected_dir)
+
+    final_clubs = [
+        club
+        for club in filtered_by_age
+        if club.get("Наименование третьего уровня РБНДО", "").strip() == selected_dir
+    ]
+
+    if not final_clubs:
+        await callback.message.edit_text("По этому направлению нет кружков.")
+    else:
+        await state.update_data(current_list=final_clubs)
+        await callback.message.edit_text(
+            f"Найдено кружков по направлению '{selected_dir}': {len(final_clubs)}\n\nВыберите:",
+            reply_markup=get_clubs_list_inline_keyboard(final_clubs),
+        )
+
+    await callback.answer()
+
+
+@dp.callback_query(lambda c: c.data.startswith("club_sel_"))
+async def process_club_select(callback: types.CallbackQuery, state: FSMContext):
+    logging.info("Выбран кружок: %s", callback.data)
+    idx_str = callback.data.replace("club_sel_", "")
+    try:
+        idx = int(idx_str)
+    except ValueError:
+        await callback.message.edit_text("Ошибка выбора.")
+        await callback.answer()
+        return
+
+    data = await state.get_data()
+    clubs = data.get("current_list", [])
+    if idx >= len(clubs):
+        await callback.message.edit_text("Кружок не найден.")
+        await callback.answer()
+        return
+
+    club = clubs[idx]
+    text = (
+        f"<b>{club.get('Наименование детского объединения', '—')}</b>\n\n"
+        f"Направление: {club.get('Наименование третьего уровня РБНДО', '—')}\n"
+        f"Возраст: {club.get('Возраст', '—')}\n"
+        f"Адрес: {club.get('Адрес предоставления услуги', 'Онлайн')}\n"
+        f"Педагог: {club.get('Педагог', 'не указан')}\n\n"
+        f"Подробнее: {club.get('Ссылка', 'ссылка отсутствует')}"
+    )
+    kb = InlineKeyboardMarkup(
+        inline_keyboard=[
+            [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_directions")],
+            [InlineKeyboardButton(text="В меню", callback_data="back_to_main")],
+        ]
+    )
+    await callback.message.edit_text(
+        text,
+        reply_markup=kb,
+        parse_mode="HTML",
+        disable_web_page_preview=True,
+    )
+    await callback.answer()
+
+
+@dp.callback_query(lambda c: c.data == "main_package")
+async def start_package(callback: types.CallbackQuery, state: FSMContext):
+    await state.set_state(PackageForm.num_people)
+    await callback.message.answer("Сколько человек в вашей группе?", reply_markup=ReplyKeyboardRemove())
+    await callback.answer()
+
+
+@dp.callback_query(lambda c: c.data == "main_masterclass")
+async def start_masterclass(callback: types.CallbackQuery, state: FSMContext):
+    await state.set_state(MasterclassForm.address)
+    await callback.message.answer("Выберите адрес:", reply_markup=get_addresses_inline_keyboard())
+    await callback.answer()
+
+
+@dp.message(PackageForm.num_people)
+async def package_num_people(message: types.Message, state: FSMContext):
+    text = message.text.strip()
+    if text == "Начать заново":
+        await state.clear()
+        await cmd_start(message)
+        return
+
+    try:
+        num = int(text)
+        if num < 1:
+            await message.answer("Введите положительное число.")
+            return
+        await state.update_data(num_people=num, selected_activities=[])
+        await state.set_state(PackageForm.activities)
+        await message.answer("Выберите 1–3 активности:", reply_markup=get_activities_keyboard())
+    except ValueError:
+        await message.answer("Пожалуйста, введите число.")
+
+
+@dp.message(PackageForm.activities)
+async def package_activities(message: types.Message, state: FSMContext):
+    text = message.text.strip()
+    if text == "Начать заново":
+        await state.clear()
+        await cmd_start(message)
+        return
+
+    if text == "Готово":
+        data = await state.get_data()
+        selected = data.get("selected_activities", [])
+        if not 1 <= len(selected) <= 3:
+            await message.answer("Выберите от 1 до 3 активностей.")
+            return
+        await state.set_state(PackageForm.name)
+        await message.answer("Как к вам обращаться? (имя)", reply_markup=ReplyKeyboardRemove())
+        return
+
+    data = await state.get_data()
+    selected = data.get("selected_activities", [])
+    module_name = text.replace(" ✅", "")
+    if module_name in PACKAGE_MODULES:
+        if module_name in selected:
+            selected.remove(module_name)
+        else:
+            if len(selected) < 3:
+                selected.append(module_name)
+            else:
+                await message.answer("Максимум 3 активности.")
+                return
+        await state.update_data(selected_activities=selected)
+        await message.answer(
+            "Выбрано: " + ", ".join(selected) if selected else "Пока ничего",
+            reply_markup=get_activities_keyboard(selected),
+        )
+
+
+@dp.message(PackageForm.name)
+async def package_name(message: types.Message, state: FSMContext):
+    text = message.text.strip()
+    if text == "Начать заново":
+        await state.clear()
+        await cmd_start(message)
+        return
+
+    await state.update_data(name=text)
+    await state.set_state(PackageForm.phone)
+    await message.answer("Ваш номер телефона для связи")
+
+
+@dp.message(PackageForm.phone)
+async def package_phone(message: types.Message, state: FSMContext):
+    text = message.text.strip()
+    if text == "Начать заново":
+        await state.clear()
+        await cmd_start(message)
+        return
+
+    await state.update_data(phone=text)
+    await state.set_state(PackageForm.date)
+    await message.answer("Желаемая дата и время (или «любое»)")
+
+
+@dp.message(PackageForm.date)
+async def package_finish(message: types.Message, state: FSMContext):
+    text = message.text.strip()
+    if text == "Начать заново":
+        await state.clear()
+        await cmd_start(message)
+        return
+
+    data = await state.get_data()
+    await state.update_data(date=text)
+
+    selected = data["selected_activities"]
+    num_act = len(selected)
+    num_p = data["num_people"]
+
+    price_idx = num_act - 1
+    total = 0
+    lines = []
+    for act in selected:
+        p = PACKAGE_MODULES[act]["prices"][price_idx]
+        cost = p * num_p
+        total += cost
+        lines.append(f"{act}: {p} ₽/чел × {num_p} = {cost} ₽")
+
+    lines_text = "\n".join(lines)
+
+    order_text = (
+        "🛒 Новый пакетный тур\n\n"
+        f"Клиент: {data.get('name')}\n"
+        f"Тел: {data.get('phone')}\n"
+        f"Дата/время: {text}\n\n"
+        f"Группа: {num_p} чел\n"
+        f"Активности ({num_act}): {', '.join(selected)}\n\n"
+        f"{lines_text}\n\n"
+        f"<b>Итого: {total} ₽</b>"
+    )
+
+    await bot.send_message(ADMIN_ID, order_text, parse_mode="HTML")
+    await message.answer("Запрос отправлен менеджерам. Скоро с вами свяжутся!", reply_markup=bottom_kb)
+    await state.clear()
+
+
+@dp.callback_query(lambda c: c.data.startswith("addr_"))
+async def choose_address(callback: types.CallbackQuery, state: FSMContext):
+    addr = callback.data.replace("addr_", "")
+    await state.update_data(address=addr)
+
+    mcs = MASTERCLASSES.get(addr, [])
+    if not mcs:
+        await callback.message.edit_text(
+            f"В данный момент на адресе «{addr}» нет запланированных мастер-классов.\n\n"
+            "Следите за обновлениями!",
+            reply_markup=InlineKeyboardMarkup(
+                inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_to_main")]]
+            ),
+        )
+    else:
+        await callback.message.edit_text(
+            "Доступные мастер-классы:", reply_markup=get_masterclasses_inline_keyboard(mcs)
+        )
+        await state.set_state(MasterclassForm.detail_view)
+
+    await callback.answer()
+
+
+@dp.callback_query(lambda c: c.data.startswith("mc_select_"))
+async def select_mc(callback: types.CallbackQuery, state: FSMContext):
+    title = callback.data.replace("mc_select_", "")
+    data = await state.get_data()
+    addr = data.get("address", "не указан")
+    mc = next((m for m in MASTERCLASSES.get(addr, []) if m["title"] == title), None)
+
+    if mc:
+        keyboard = get_mc_actions_inline_keyboard(title)
+        await callback.message.edit_text(
+            f"{mc['title']}\n"
+            f"Когда: {mc['date']} в {mc['time']}\n"
+            f"Стоимость: {mc['price']} ₽\n"
+            f"Адрес: {addr}",
+            reply_markup=keyboard,
+        )
+
+    await callback.answer()
+
+
+@dp.callback_query(lambda c: c.data.startswith("mc_detail_"))
+async def mc_detail(callback: types.CallbackQuery):
+    title = callback.data.replace("mc_detail_", "")
+    mc = next((m for addr in MASTERCLASSES for m in MASTERCLASSES[addr] if m["title"] == title), None)
+    if mc:
+        await callback.message.answer(
+            f"Подробное описание:\n{mc['description_link']}", disable_web_page_preview=False
+        )
+    await callback.answer()
+
+
+@dp.callback_query(lambda c: c.data.startswith("mc_signup_"))
+async def mc_signup(callback: types.CallbackQuery, state: FSMContext):
+    title = callback.data.replace("mc_signup_", "")
+    mc = next((m for addr in MASTERCLASSES for m in MASTERCLASSES[addr] if m["title"] == title), None)
+    if mc:
+        await state.update_data(selected_mc=mc)
+        await state.set_state(MasterclassForm.name)
+        await callback.message.answer(
+            f"Запись на «{mc['title']}»\n\nКак к вам обращаться? (имя)",
+            reply_markup=ReplyKeyboardRemove(),
+        )
+    await callback.answer()
+
+
+@dp.callback_query(
+    lambda c: c.data
+    in [
+        "back_to_main",
+        "back_to_addresses",
+        "back_to_mcs",
+        "back_to_clubs_addresses",
+        "back_to_directions",
+    ]
+)
+async def back_callback(callback: types.CallbackQuery, state: FSMContext):
+    data = callback.data
+
+    if data == "back_to_main":
+        await state.clear()
+        await callback.message.edit_text("Выберите действие:", reply_markup=get_main_inline_keyboard())
+
+    elif data == "back_to_addresses":
+        await state.set_state(MasterclassForm.address)
+        await callback.message.edit_text("Выберите адрес:", reply_markup=get_addresses_inline_keyboard())
+
+    elif data == "back_to_mcs":
+        user_data = await state.get_data()
+        addr = user_data.get("address", "не указан")
+        mcs = MASTERCLASSES.get(addr, [])
+        await callback.message.edit_text(
+            "Доступные мастер-классы:", reply_markup=get_masterclasses_inline_keyboard(mcs)
+        )
+
+    elif data == "back_to_clubs_addresses":
+        await state.set_state(ClubsForm.address)
+        await callback.message.edit_text(
+            "Выберите адрес:", reply_markup=get_clubs_addresses_inline_keyboard()
+        )
+
+    elif data == "back_to_directions":
+        user_data = await state.get_data()
+        clubs = user_data.get("filtered_by_age", [])
+        await callback.message.edit_text(
+            "Выберите направление:", reply_markup=get_direction_keyboard(clubs)
+        )
+
+    await callback.answer()
+
+
+@dp.message(MasterclassForm.name)
+async def mc_name(message: types.Message, state: FSMContext):
+    await state.update_data(name=message.text.strip())
+    await state.set_state(MasterclassForm.phone)
+    await message.answer("Ваш номер телефона для связи")
+
+
+@dp.message(MasterclassForm.phone)
+async def mc_phone(message: types.Message, state: FSMContext):
+    data = await state.get_data()
+    mc = data.get("selected_mc")
+    addr = data.get("address", "не указан")
+
+    if not mc:
+        await message.answer(
+            "Ошибка: данные мастер-класса не найдены. Начните заново.", reply_markup=bottom_kb
+        )
+        await state.clear()
+        return
+
+    order_text = (
+        "🛒 НОВАЯ ЗАЯВКА НА МАСТЕР-КЛАСС\n\n"
+        f"Мастер-класс: {mc['title']}\n"
+        f"Дата и время: {mc['date']} {mc['time']}\n"
+        f"Адрес: {addr}\n"
+        f"Стоимость: {mc['price']} ₽\n"
+        f"Описание: {mc['description_link']}\n\n"
+        f"Клиент: {data.get('name', 'не указано')}\n"
+        f"Телефон: {message.text.strip()}"
+    )
+
+    await bot.send_message(ADMIN_ID, order_text, parse_mode="HTML", disable_web_page_preview=False)
+
+    await message.answer(
+        f"Вы записаны на «{mc['title']}»!\n"
+        "Менеджер свяжется с вами в ближайшее время для подтверждения.\n\n"
+        f"Подробности: {mc['description_link']}",
+        reply_markup=bottom_kb,
+        disable_web_page_preview=False,
+    )
+    await state.clear()
+
+
+async def main():
+    try:
+        me = await bot.get_me()
+        logging.info("Бот запущен как @%s", me.username)
+        await bot.delete_webhook(drop_pending_updates=True)
+    except Exception as exc:
+        logging.error("Ошибка запуска: %s", exc)
+
+    await dp.start_polling(bot)
+
+
+if __name__ == "__main__":
+    asyncio.run(main())
 
EOF
)
