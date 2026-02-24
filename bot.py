import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ──────────────────────────────────────────────
TOKEN = "8606369205:AAEc80Rdnvg8fuogozkrc3VtqbZg9zZjG1E"
ADMIN_ID = 6748745225  # @dyutsvictoriya
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

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
            "description_link": "https://t.me/dyutsvictory/3726"
        }
        # Добавляй новые мастер-классы по адресу
    ],
    "СП Щербинка":      [],
    "МХС Аннино":       [],
    "СП Юный техник":   [],
}

ADDRESSES = list(MASTERCLASSES.keys())

class MasterclassForm(StatesGroup):
    address      = State()
    detail_view  = State()
    name         = State()
    phone        = State()

# ─── КЛАВИАТУРЫ ──────────────────────────────────────────────────────────────

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Пакетные туры")
    builder.button(text="Мастер-классы")
    builder.button(text="Написать в поддержку")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

main_kb = get_main_keyboard()

def get_back_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Назад")
    return builder.as_markup(resize_keyboard=True)

def get_addresses_keyboard():
    builder = ReplyKeyboardBuilder()
    for addr in ADDRESSES:
        builder.button(text=addr)
    builder.button(text="Назад")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_activities_keyboard(selected=None):
    selected = selected or []
    builder = ReplyKeyboardBuilder()
    for module in PACKAGE_MODULES:
        text = f"{module} {'✅' if module in selected else ''}"
        builder.button(text=text)
    builder.button(text="Готово")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# ─── СТАРТ И ГЛАВНОЕ МЕНЮ ───────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Здравствуйте, я бот Центра «Виктория».\n\n"
        "Здесь можно подобрать пакетный тур или записаться на мастер-класс.",
        reply_markup=main_kb
    )

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
    await message.answer("Сообщение отправлено администратору. Спасибо!")
    await state.clear()
    await message.answer("Вернуться в меню?", reply_markup=main_kb)

# ─── ПАКЕТНЫЕ ТУРЫ ───────────────────────────────────────────────────────────

@dp.message(lambda m: m.text == "Пакетные туры")
async def start_package(message: types.Message, state: FSMContext):
    await state.set_state(PackageForm.num_people)
    await message.answer("Сколько человек в вашей группе?", reply_markup=ReplyKeyboardRemove())

@dp.message(PackageForm.num_people)
async def package_num_people(message: types.Message, state: FSMContext):
    try:
        num = int(message.text.strip())
        if num < 1:
            await message.answer("Введите положительное число.")
            return
        await state.update_data(num_people=num, selected_activities=[])
        await state.set_state(PackageForm.activities)
        await message.answer("Выберите 1–3 активности:", reply_markup=get_activities_keyboard())
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@dp.message(PackageForm.activities)
async def package_activities(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "Готово":
        data = await state.get_data()
        selected = data.get("selected_activities", [])
        if not 1 <= len(selected) <= 3:
            await message.answer("Выберите от 1 до 3 активностей.")
            return
        await state.set_state(PackageForm.name)
        await message.answer("Как к вам обращаться? (имя)", reply_markup=ReplyKeyboardRemove())
        return

    data = await state.get_data()
    selected = data.get("selected_activities", [])
    module_name = text.replace(" ✅", "")
    if module_name in PACKAGE_MODULES:
        if module_name in selected:
            selected.remove(module_name)
        else:
            if len(selected) < 3:
                selected.append(module_name)
            else:
                await message.answer("Максимум 3 активности.")
                return
        await state.update_data(selected_activities=selected)
        await message.answer(
            "Выбрано: " + ", ".join(selected) if selected else "Пока ничего",
            reply_markup=get_activities_keyboard(selected)
        )

@dp.message(PackageForm.name)
async def package_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(PackageForm.phone)
    await message.answer("Ваш номер телефона для связи")

@dp.message(PackageForm.phone)
async def package_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await state.set_state(PackageForm.date)
    await message.answer("Желаемая дата и время (или «любое»)")

@dp.message(PackageForm.date)
async def package_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(date=message.text.strip())

    selected = data["selected_activities"]
    num_act = len(selected)
    num_p = data["num_people"]

    price_idx = num_act - 1
    total = 0
    lines = []
    for act in selected:
        p = PACKAGE_MODULES[act]["prices"][price_idx]
        cost = p * num_p
        total += cost
        lines.append(f"{act}: {p} ₽/чел × {num_p} = {cost} ₽")

    lines_text = "\n".join(lines)

    order_text = (
        "🛒 Новый пакетный тур\n\n"
        f"Клиент: {data.get('name')}\n"
        f"Тел: {data.get('phone')}\n"
        f"Дата/время: {data.get('date')}\n\n"
        f"Группа: {num_p} чел\n"
        f"Активности ({num_act}): {', '.join(selected)}\n\n"
        f"{lines_text}\n\n"
        f"<b>Итого: {total} ₽</b>"
    )

    for name, uid in MANAGERS.items():
        try:
            await bot.send_message(uid, order_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка отправки {name} ({uid}): {e}")

    await message.answer("Запрос отправлен менеджерам. Скоро с вами свяжутся!", reply_markup=main_kb)
    await state.clear()

# ─── МАСТЕР-КЛАССЫ ───────────────────────────────────────────────────────────

@dp.message(lambda m: m.text == "Мастер-классы")
async def mc_start(message: types.Message, state: FSMContext):
    await state.set_state(MasterclassForm.address)
    await message.answer("Выберите адрес:", reply_markup=get_addresses_keyboard())

@dp.message(MasterclassForm.address)
async def mc_choose_address(message: types.Message, state: FSMContext):
    addr = message.text.strip()
    if addr == "Назад":
        await state.clear()
        await message.answer("Вернулись в главное меню", reply_markup=main_kb)
        return

    if addr not in ADDRESSES:
        await message.answer("Выберите адрес из списка.", reply_markup=get_addresses_keyboard())
        return

    await state.update_data(address=addr)

    mcs = MASTERCLASSES.get(addr, [])
    if not mcs:
        await message.answer(
            f"В данный момент на адресе «{addr}» нет запланированных мастер-классов.\n\n"
            "Следите за обновлениями!",
            reply_markup=get_back_keyboard()
        )
        return

    builder = ReplyKeyboardBuilder()
    for mc in mcs:
        builder.button(text=mc["title"])
    builder.button(text="Назад")
    builder.adjust(1)

    await message.answer("Доступные мастер-классы:", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(MasterclassForm.detail_view)

@dp.message(MasterclassForm.detail_view)
async def mc_select_class(message: types.Message, state: FSMContext):
    title = message.text.strip()
    if title == "Назад":
        await state.set_state(MasterclassForm.address)
        await message.answer("Выберите адрес:", reply_markup=get_addresses_keyboard())
        return

    data = await state.get_data()
    addr = data["address"]
    mc = next((m for m in MASTERCLASSES.get(addr, []) if m["title"] == title), None)

    if not mc:
        await message.answer("Выберите мастер-класс из списка.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подробнее", callback_data=f"mc_detail_{title}")],
        [InlineKeyboardButton(text="Записаться", callback_data=f"mc_signup_{title}")],
        [InlineKeyboardButton(text="Назад", callback_data="mc_back")]
    ])

    await message.answer(
        f"{mc['title']}\n"
        f"Когда: {mc['date']} в {mc['time']}\n"
        f"Стоимость: {mc['price']} ₽\n"
        f"Адрес: {addr}",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("mc_") or c.data == "mc_back")
async def mc_callback(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "mc_back":
        await callback.message.delete()
        await state.set_state(MasterclassForm.address)
        await callback.message.answer("Выберите адрес:", reply_markup=get_addresses_keyboard())
        await callback.answer()
        return

    if data.startswith("mc_detail_"):
        title = data.replace("mc_detail_", "")
        mc = next((m for addr in MASTERCLASSES for m in MASTERCLASSES[addr] if m["title"] == title), None)
        if mc:
            await callback.message.answer(f"Подробное описание:\n{mc['description_link']}")
        await callback.answer()

    elif data.startswith("mc_signup_"):
        title = data.replace("mc_signup_", "")
        mc = next((m for addr in MASTERCLASSES for m in MASTERCLASSES[addr] if m["title"] == title), None)
        if mc:
            await state.update_data(selected_mc=mc)
            await state.set_state(MasterclassForm.name)
            await callback.message.answer(
                f"Запись на «{mc['title']}»\n\nКак к вам обращаться? (имя)",
                reply_markup=ReplyKeyboardRemove()
            )
        await callback.answer()

@dp.message(MasterclassForm.name)
async def mc_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(MasterclassForm.phone)
    await message.answer("Ваш номер телефона для связи")

@dp.message(MasterclassForm.phone)
async def mc_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mc = data["selected_mc"]

    order_text = (
        f"🛒 Запись на мастер-класс\n\n"
        f"Мастер-класс: {mc['title']}\n"
        f"Дата и время: {mc['date']} {mc['time']}\n"
        f"Адрес: {mc['address']}\n"
        f"Стоимость: {mc['price']} ₽\n"
        f"Описание: {mc['description_link']}\n\n"
        f"Клиент: {data.get('name')}\n"
        f"Телефон: {message.text.strip()}"
    )

    for name, uid in MANAGERS.items():
        try:
            await bot.send_message(uid, order_text, parse_mode="HTML", disable_web_page_preview=False)
        except Exception as e:
            logger.error(f"Ошибка отправки {name}: {e}")

    await message.answer(
        f"Вы записаны на «{mc['title']}»!\n"
        "Менеджер свяжется с вами для подтверждения.\n\n"
        f"Подробности: {mc['description_link']}",
        reply_markup=main_kb,
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
