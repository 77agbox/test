from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import ADMIN_ID
from keyboards import main_menu

router = Router()

PACKAGE_MODULES = {
    "Картинг": [2200, 2100, 2000],
    "Симрейсинг": [1600, 1500, 1400],
    "Практическая стрельба": [1600, 1500, 1400],
    "Лазертаг": [1600, 1500, 1400],
    "Керамика": [1600, 1500, 1400],
    "Мягкая игрушка": [1300, 1200, 1100],
}


class PackageForm(StatesGroup):
    people = State()
    activities = State()
    name = State()
    phone = State()


def activities_keyboard(selected=None):
    selected = selected or []
    rows = []
    for name in PACKAGE_MODULES:
        label = f"✅ {name}" if name in selected else name
        rows.append([InlineKeyboardButton(text=label, callback_data=f"act_{name}")])

    rows.append([InlineKeyboardButton(text="🟢 Готово", callback_data="act_done")])
    rows.append([InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(lambda c: c.data == "m_package")
async def start_package(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PackageForm.people)
    await callback.message.edit_text(
        "👥 <b>Пакетные туры</b>\n\n"
        "Введите количество человек.\n"
        "<i>Минимально — от 5 человек.</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(PackageForm.people)
async def get_people(message: types.Message, state: FSMContext):
    try:
        people = int(message.text)
        if people < 5:
            await message.answer("❗ Минимум 5 человек.")
            return
    except ValueError:
        await message.answer("Введите число.")
        return

    await state.update_data(people=people, selected=[])
    await state.set_state(PackageForm.activities)

    await message.answer(
        "🎯 <b>Выберите от 1 до 3 активностей:</b>",
        parse_mode="HTML",
        reply_markup=activities_keyboard(),
    )


@router.callback_query(PackageForm.activities, lambda c: c.data.startswith("act_"))
async def choose_activity(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", [])
    activity = callback.data.replace("act_", "")

    if activity in PACKAGE_MODULES:
        if activity in selected:
            selected.remove(activity)
        else:
            if len(selected) >= 3:
                await callback.answer("Можно выбрать максимум 3 активности.", show_alert=True)
                return
            selected.append(activity)

    await state.update_data(selected=selected)
    await callback.message.edit_reply_markup(reply_markup=activities_keyboard(selected))
    await callback.answer()


@router.callback_query(PackageForm.activities, lambda c: c.data == "act_done")
async def activities_done(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", [])

    if not 1 <= len(selected) <= 3:
        await callback.answer("Выберите от 1 до 3 активностей.", show_alert=True)
        return

    await state.set_state(PackageForm.name)
    await callback.message.edit_text("📝 Ваше имя:")
    await callback.answer()


@router.message(PackageForm.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(PackageForm.phone)
    await message.answer("📞 Телефон для связи:")


@router.message(PackageForm.phone)
async def finish_package(message: types.Message, state: FSMContext):
    data = await state.get_data()

    people = data["people"]
    selected = data["selected"]
    name = data["name"]
    phone = message.text.strip()

    price_index = len(selected) - 1

    total = 0
    per_person_total = 0
    lines = []

    for act in selected:
        price_per_person = PACKAGE_MODULES[act][price_index]
        cost = price_per_person * people
        per_person_total += price_per_person
        total += cost
        lines.append(f"• {act}: <b>{price_per_person} ₽</b> с человека")

    activities_text = "\n".join(lines)

    username_link = (
        f'<a href="https://t.me/{message.from_user.username}">@{message.from_user.username}</a>'
        if message.from_user.username
        else "без username"
    )

    await message.bot.send_message(
        ADMIN_ID,
        f"🛒 <b>Новая заявка на пакетный тур</b>\n\n"
        f"<b>Клиент:</b> {name}\n"
        f"<b>Телефон:</b> {phone}\n"
        f"<b>Профиль:</b> {username_link}\n"
        f"<b>TG ID:</b> {message.from_user.id}\n\n"
        f"<b>Группа:</b> {people} человек\n"
        f"<b>Активности:</b> {', '.join(selected)}\n\n"
        f"{activities_text}\n\n"
        f"<b>Итого с человека:</b> {per_person_total} ₽\n"
        f"<b>Общая сумма:</b> {total} ₽",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    await message.answer(
        f"✅ <b>Ваша заявка принята!</b>\n\n"
        f"<b>Количество человек:</b> {people}\n"
        f"<b>Активности:</b> {', '.join(selected)}\n\n"
        f"<b>Стоимость услуг:</b>\n"
        f"{activities_text}\n\n"
        f"💰 <b>Стоимость с человека: {per_person_total} ₽</b>\n"
        f"👥 <b>Общая сумма для группы: {total} ₽</b>\n\n"
        f"С вами скоро свяжется администратор.",
        parse_mode="HTML",
        reply_markup=main_menu(is_admin=(message.from_user.id == ADMIN_ID)),
    )

    await state.clear()
