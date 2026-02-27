from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu(is_admin=False):
    """
    Главное меню. Если администратор, то добавляется кнопка для админ-панели.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.insert(InlineKeyboardButton(text="🎓 Кружки", callback_data="m_clubs"))
    keyboard.insert(InlineKeyboardButton(text="🎯 Пакетные туры", callback_data="m_package"))
    keyboard.insert(InlineKeyboardButton(text="🎨 Мастер-классы", callback_data="m_master"))

    if is_admin:
        keyboard.insert(InlineKeyboardButton(text="⚙ Админ-панель", callback_data="admin_panel"))

    return keyboard
