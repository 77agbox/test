from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Кружки", callback_data="m_clubs")],
            [InlineKeyboardButton(text="Пакетные туры", callback_data="m_package")],
            [InlineKeyboardButton(text="Мастер-классы", callback_data="m_master")],
        ]
    )


def bottom_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Начать заново")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
