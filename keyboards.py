from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# ================= ГЛАВНОЕ МЕНЮ =================

def main_menu():
    buttons = [
        ("🎓 Кружки", "m_clubs"),
        ("🎯 Пакетные туры", "m_package"),
        ("🎨 Мастер-классы", "m_master"),
    ]

    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=data)]
        for text, data in buttons
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ================= НИЖНЯЯ КЛАВИАТУРА =================

def bottom_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🏠 Начать заново")
    builder.button(text="✉ Написать в поддержку")
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


# ================= КНОПКА НАЗАД =================

def back_to_menu_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="back_main")]
        ]
    )
