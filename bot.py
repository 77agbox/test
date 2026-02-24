import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ──────────────────────────────────────────────
TOKEN = "8606369205:AAEc80Rdnvg8fuogozkrc3VtqbZg9zZjG1E"
ADMIN_ID = 462740408  # @sergienkoalvl — сюда приходят заявки и поддержка
# ──────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

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
    num_people   = State()
    activities   = State()
    name         = State()
    phone        = State()
    date         = State()

# ─── МАСТЕР-КЛАССЫ ───────────────────────────────────────────────────────────

MASTERCLASSES = {
    "Газопровод д.4": [
        {
            "title": "Сумочка для телефона",
            "date": "04.03.2026",
            "time": "17:00",
            "price": 1500,
            "description_link": "https://t.me/dyutsvictory/3733"
        },
        {
            "title": "Сумочка для телефона",
            "date": "26.02.2026",
            "time": "17:00",
            "price": 1500,
            "description_link": "https://t.me/dyutsvictory/3733"
        }
    ],
    "СП Щербинка":      [],
    "МХС Аннино":       [],
    "СП Юный техник":   [],
}

ADDRESSES = list(MASTERCLASSES.keys())

class MasterclassForm(StatesGroup):
    address      = State()
    list_view    = State()
    detail_view  = State()
    name         = State()
    phone        = State()

# ─── КЛАВИАТУРЫ ──────────────────────────────────────────────────────────────

def get_bottom_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Начать заново")
    builder.button(text="Написать в поддержку")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

bottom_kb = get_bottom_keyboard()

def get_main_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пакетные туры", callback_data="main_package")],
        [InlineKeyboardButton(text="Мастер-классы", callback_data="main_masterclass")]
    ])
    return keyboard

def get_addresses_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for addr in ADDRESSES:
        count = len(MASTERCLASSES.get(addr, []))
        text = f"{addr} ({count})" if count > 0 else addr
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=text, callback_data=f"addr_{addr}")
        ])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_main")
    ])
    return keyboard

def get_masterclasses_inline_keyboard(mcs):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for mc in mcs:
        text = f"{mc['title']} — {mc['date']}"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=text, callback_data=f"mc_select_{mc['title']}")
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_addresses")
    ])
    return keyboard

def get_mc_actions_inline_keyboard(title):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подробнее", callback_data=f"mc_detail_{title}")],
        [InlineKeyboardButton(text="Записаться", callback_data=f"mc_signup_{title}")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_mcs")]
    ])
    return keyboard

# ─── СТАРТ ───────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Здравствуйте, я бот Центра «Виктория».\n\n"
        "Здесь можно подобрать пакетный тур или записаться на мастер-класс.",
        reply_markup=bottom_kb
    )
    await message.answer("Выберите действие:", reply_markup=get_main_inline_keyboard())

# ─── НАЧАТЬ ЗАНОВО ───────────────────────────────────────────────────────────

@dp.message(lambda m: m.text == "Начать заново")
async def restart(message: types.Message, state: FSMContext):
    await state.clear()
    await cmd_start(message)

# ─── НАПИСАТЬ В ПОДДЕРЖКУ ───────────────────────────────────────────────────

@dp.message(lambda m: m.text == "Написать в поддержку")
async def start_support(message: types.Message, state: FSMContext):
    await message.answer(
        "Напишите ваше сообщение, и оно будет отправлено администратору.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state("support_message")

@dp.message(StateFilter("support_message"))
async def forward_to_support(message: types.Message, state: FSMContext):
    await bot.send_message(
        ADMIN_ID,
        f"Сообщение от {message.from_user.full_name} (@{message.from_user.username or 'нет'}):\n\n"
        f"{message.text}"
    )
    await message.answer("Сообщение отправлено администратору. Спасибо!", reply_markup=bottom_kb)
    await state.clear()

# ─── ГЛАВНОЕ МЕНЮ (инлайн) ──────────────────────────────────────────────────

@dp.callback_query(lambda c: c.data.startswith("main_"))
async def main_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "main_package":
        await state.set_state(PackageForm.num_people)
        await callback.message.edit_text("Сколько человек в вашей группе?", reply_markup=ReplyKeyboardRemove())
    elif data == "main_masterclass":
        await state.set_state(MasterclassForm.address)
        await callback.message.edit_text("Выберите адрес:", reply_markup=get_addresses_inline_keyboard())

    await callback.answer()

# ─── МАСТЕР-КЛАССЫ ───────────────────────────────────────────────────────────

@dp.callback_query(lambda c: c.data.startswith("addr_"))
async def choose_address(callback: types.CallbackQuery, state: FSMContext):
    addr = callback.data.replace("addr_", "")
    await state.update_data(address=addr)  # ← сохраняем адрес в состояние

    mcs = MASTERCLASSES.get(addr, [])
    if not mcs:
        await callback.message.edit_text(
            f"В данный момент на адресе «{addr}» нет запланированных мастер-классов.\n\n"
            "Следите за обновлениями!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
            ])
        )
    else:
        await callback.message.edit_text(
            "Доступные мастер-классы:",
            reply_markup=get_masterclasses_inline_keyboard(mcs)
        )
        await state.set_state(MasterclassForm.detail_view)

    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("mc_select_"))
async def select_mc(callback: types.CallbackQuery, state: FSMContext):
    title = callback.data.replace("mc_select_", "")
    data = await state.get_data()
    addr = data.get("address", "неизвестно")  # ← берём адрес из состояния
    mc = next((m for m in MASTERCLASSES.get(addr, []) if m["title"] == title), None)

    if mc:
        keyboard = get_mc_actions_inline_keyboard(title)
        await callback.message.edit_text(
            f"{mc['title']}\n"
            f"Когда: {mc['date']} в {mc['time']}\n"
            f"Стоимость: {mc['price']} ₽\n"
            f"Адрес: {addr}",
            reply_markup=keyboard
        )

    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("mc_detail_"))
async def mc_detail(callback: types.CallbackQuery):
    title = callback.data.replace("mc_detail_", "")
    mc = next((m for addr in MASTERCLASSES for m in MASTERCLASSES[addr] if m["title"] == title), None)
    if mc:
        await callback.message.answer(f"Подробное описание:\n{mc['description_link']}", disable_web_page_preview=False)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("mc_signup_"))
async def mc_signup(callback: types.CallbackQuery, state: FSMContext):
    title = callback.data.replace("mc_signup_", "")
    mc = next((m for addr in MASTERCLASSES for m in MASTERCLASSES[addr] if m["title"] == title), None)
    if mc:
        await state.update_data(selected_mc=mc)
        await state.set_state(MasterclassForm.name)
        await callback.message.answer(
            f"Запись на «{mc['title']}»\n\nКак к вам обращаться? (имя)",
            reply_markup=ReplyKeyboardRemove()
        )
    await callback.answer()

@dp.callback_query(lambda c: c.data in ["back_to_main", "back_to_addresses", "back_to_mcs"])
async def back_callback(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "back_to_main":
        await state.clear()
        await callback.message.edit_text(
            "Выберите действие:",
            reply_markup=get_main_inline_keyboard()
        )

    elif data == "back_to_addresses":
        await state.set_state(MasterclassForm.address)
        await callback.message.edit_text(
            "Выберите адрес:",
            reply_markup=get_addresses_inline_keyboard()
        )

    elif data == "back_to_mcs":
        data = await state.get_data()
        addr = data.get("address", "неизвестно")
        mcs = MASTERCLASSES.get(addr, [])
        await callback.message.edit_text(
            "Доступные мастер-классы:",
            reply_markup=get_masterclasses_inline_keyboard(mcs)
        )

    await callback.answer()

# ─── АНКЕТА МАСТЕР-КЛАССОВ ──────────────────────────────────────────────────

@dp.message(MasterclassForm.name)
async def mc_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(MasterclassForm.phone)
    await message.answer("Ваш номер телефона для связи")

@dp.message(MasterclassForm.phone)
async def mc_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mc = data.get("selected_mc")

    if not mc:
        await message.answer("Ошибка: данные мастер-класса не найдены. Начните заново.", reply_markup=bottom_kb)
        await state.clear()
        return

    order_text = (
        f"🛒 НОВАЯ ЗАЯВКА НА МАСТЕР-КЛАСС\n\n"
        f"Мастер-класс: {mc['title']}\n"
        f"Дата и время: {mc['date']} {mc['time']}\n"
        f"Адрес: {data.get('address', 'не указан')}\n"
        f"Стоимость: {mc['price']} ₽\n"
        f"Описание: {mc['description_link']}\n\n"
        f"Клиент: {data.get('name', 'не указано')}\n"
        f"Телефон: {message.text.strip()}"
    )

    await bot.send_message(ADMIN_ID, order_text, parse_mode="HTML", disable_web_page_preview=False)

    await message.answer(
        f"Вы записаны на «{mc['title']}»!\n"
        "Менеджер свяжется с вами в ближайшее время для подтверждения.\n\n"
        f"Подробности: {mc['description_link']}",
        reply_markup=bottom_kb,
        disable_web_page_preview=False
    )
    await state.clear()

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
