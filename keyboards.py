from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# ===== Главное меню =====
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


# ===== Нижняя клавиатура =====
def bottom_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🏠 Начать заново")
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


# ===== Кнопка "Назад в меню" (на будущее) =====
def back_to_menu_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="back_main")]
        ]
    )
