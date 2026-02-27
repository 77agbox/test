from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# ================= ГЛАВНОЕ МЕНЮ =================

def main_menu(is_admin: bool = False):
    """
    Главное меню.
    Если пользователь админ — добавляется кнопка админ-панели.
    """

    buttons = [
        ("🎓 Кружки", "m_clubs"),
        ("🎯 Пакетные туры", "m_package"),
        ("🎨 Мастер-классы", "m_master"),
    ]

    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=data)]
        for text, data in buttons
    ]

    # Если админ — добавляем кнопку админ-панели
    if is_admin:
        keyboard.append(
            [InlineKeyboardButton(text="⚙ Админ-панель", callback_data="admin_panel")]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ================= НИЖНЯЯ КЛАВИАТУРА =================

def bottom_kb(is_admin: bool = False):
    """
    Нижняя клавиатура (Reply).
    Всегда:
    - Начать заново
    - Написать в поддержку

    Если админ — добавляется кнопка админ-панели.
    """

    builder = ReplyKeyboardBuilder()

    builder.button(text="🏠 Начать заново")
    builder.button(text="✉ Написать в поддержку")

    if is_admin:
        builder.button(text="⚙ Админ-панель")

    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


# ================= КНОПКА НАЗАД =================

def back_to_menu_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="back_main")]
        ]
    )
