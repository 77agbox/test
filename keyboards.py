from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🎓 Кружки", callback_data="m_clubs")],
        [InlineKeyboardButton(text="🎯 Пакетные туры", callback_data="m_package")],
        [InlineKeyboardButton(text="🎨 Мастер-классы", callback_data="m_master")],
        [InlineKeyboardButton(text="🏠 Начать заново", callback_data="back_main")],
        [InlineKeyboardButton(text="✉ Написать в поддержку", callback_data="support_start")],
    ]

    if is_admin:
        keyboard.append([InlineKeyboardButton(text="⚙ Админ-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
