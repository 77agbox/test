from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_menu(is_admin=False):
    """
    Главное меню. Если администратор, то добавляется кнопка для админ-панели.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Кружки", callback_data="m_clubs")],
            [InlineKeyboardButton(text="🎯 Пакетные туры", callback_data="m_package")],
            [InlineKeyboardButton(text="🎨 Мастер-классы", callback_data="m_master")]
        ]
    )
    
    if is_admin:
        keyboard.add(InlineKeyboardButton(text="⚙ Админ-панель", callback_data="admin_panel"))

    return keyboard

def bottom_kb(is_admin=False):
    """
    Нижняя клавиатура (Reply).
    Всегда:
    - Начать заново
    - Написать в поддержку
    """
    builder = ReplyKeyboardBuilder()

    builder.button(text="🏠 Начать заново")
    builder.button(text="✉ Написать в поддержку")
    
    if is_admin:
        builder.button(text="⚙ Админ-панель")

    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)
