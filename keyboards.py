from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# ======================= Главное меню =======================
def main_menu(is_admin=False):
    """
    Главное меню. Если администратор, то добавляется кнопка для админ-панели.
    Все кнопки в главном меню, включая "Написать в поддержку", "Начать заново" и другие.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Кружки", callback_data="m_clubs")],
            [InlineKeyboardButton(text="🎯 Пакетные туры", callback_data="m_package")],
            [InlineKeyboardButton(text="🎨 Мастер-классы", callback_data="m_master")]
        ]
    )

    # Если админ, добавляем кнопку админ-панели
    if is_admin:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⚙ Админ-панель", callback_data="admin_panel")])

    return keyboard


# ======================= Клавиатура для кнопок "Начать заново" и "Написать в поддержку" =======================
def bottom_kb(is_subscribed=False, is_admin=False):
    """
    Нижняя клавиатура теперь не содержит кнопок, оставим их в главном меню.
    """
    builder = ReplyKeyboardBuilder()

    if not is_admin:
        if is_subscribed:
            builder.button(text="❌ Отписаться от рассылки")  # Кнопка для отписки, если подписан
        else:
            builder.button(text="📢 Подписаться на рассылку")  # Кнопка для подписки, если не подписан

    builder.button(text="✉ Написать в поддержку")  # Кнопка для написания в поддержку
    builder.button(text="🏠 Начать заново")  # Кнопка для перезапуска бота

    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
