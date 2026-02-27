from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# ======================= Главное меню =======================
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
        # Добавляем кнопку "Админ-панель", если пользователь админ
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⚙ Админ-панель", callback_data="admin_panel")])

    return keyboard


# ======================= Нижняя клавиатура (Reply) =======================
def bottom_kb(is_subscribed=False, is_admin=False):
    """
    Нижняя клавиатура. Отображает кнопки в зависимости от подписки и роли пользователя.
    """
    builder = ReplyKeyboardBuilder()

    builder.button(text="🏠 Начать заново")  # Кнопка для начала заново
    builder.button(text="✉ Написать в поддержку")  # Кнопка для отправки сообщения в поддержку
    
    if not is_admin:
        if is_subscribed:
            builder.button(text="❌ Отписаться от рассылки")  # Кнопка для отписки, если подписан
        else:
            builder.button(text="📢 Подписаться на рассылку")  # Кнопка для подписки, если не подписан

    if is_admin:
        builder.button(text="⚙ Админ-панель")  # Кнопка для админ-панели, если админ

    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


# ======================= Клавиатура для выбора адресов (для кружков) =======================
def get_club_addresses_inline_keyboard():
    """
    Клавиатура для выбора адресов.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Газопровод, д.4", callback_data="addr_gazoprovod")],
            [InlineKeyboardButton(text="МХС Аннино", callback_data="addr_annino")],
            [InlineKeyboardButton(text="СП Щербинка", callback_data="addr_scherbinka")],
            [InlineKeyboardButton(text="СП Юный техник", callback_data="addr_molodoy_tekhnik")],
            [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_main")]  # Кнопка "Назад"
        ]
    )


# ======================= Клавиатура для выбора мастер-классов =======================
def get_masterclasses_inline_keyboard():
    """
    Клавиатура для выбора мастер-классов.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мастер-класс 1", callback_data="mc_select_1")],
            [InlineKeyboardButton(text="Мастер-класс 2", callback_data="mc_select_2")],
            [InlineKeyboardButton(text="Мастер-класс 3", callback_data="mc_select_3")],
            [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_main")]  # Кнопка "Назад"
        ]
    )


# ======================= Клавиатура для админ-панели =======================
def get_admin_panel_keyboard():
    """
    Клавиатура для админ-панели
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить мастер-класс", callback_data="admin_add")],
            [InlineKeyboardButton(text="➖ Удалить мастер-класс", callback_data="admin_delete")],
            [InlineKeyboardButton(text="📢 Отправить рассылку", callback_data="send_broadcast")],
            [InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")]  # Кнопка "Назад"
        ]
    )


# ======================= Клавиатура для возврата в главное меню =======================
def get_back_to_main_keyboard():
    """
    Клавиатура для возврата в главное меню.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Назад", callback_data="back_main")]  # Кнопка "Назад"
        ]
    )


# ======================= Клавиатура для выбора направления кружков =======================
def get_direction_keyboard():
    """
    Клавиатура для выбора направления кружков.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Керамика", callback_data="dir_keramika")],
            [InlineKeyboardButton(text="Симрейсинг", callback_data="dir_simracing")],
            [InlineKeyboardButton(text="Лазертаг", callback_data="dir_laser")],
            [InlineKeyboardButton(text="Подсвечники", callback_data="dir_subs")],
            [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_clubs")]  # Кнопка "Назад"
        ]
    )
