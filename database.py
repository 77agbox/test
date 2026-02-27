import sqlite3
from contextlib import closing
from config import DB_NAME


# ================= ИНИЦИАЛИЗАЦИЯ ТАБЛИЦ =================

def init_db():
    """
    Инициализация всех таблиц базы данных.
    """
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS masterclasses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    place TEXT,
                    description TEXT,
                    teacher TEXT,
                    date TEXT,
                    price TEXT,
                    link TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    name TEXT,
                    phone TEXT,
                    subscribed INTEGER DEFAULT 1
                )
            """)


# ================= ФУНКЦИИ ДЛЯ МАСТЕР-КЛАССОВ =================

def add_masterclass(data):
    """
    Добавить новый мастер-класс в базу данных.
    """
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("""
                INSERT INTO masterclasses (title, place, description, teacher, date, price, link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data["title"],
                data["place"],
                data["description"],
                data["teacher"],
                data["date"],
                data["price"],
                data["link"]
            ))


def get_masterclasses():
    """
    Получить все мастер-классы.
    """
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM masterclasses")
        return cur.fetchall()


def delete_masterclass(mc_id):
    """
    Удалить мастер-класс из базы данных.
    """
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("DELETE FROM masterclasses WHERE id = ?", (mc_id,))


# ================= ФУНКЦИИ ДЛЯ ПОДПИСЧИКОВ =================

def add_subscriber(user_id: int, name: str, phone: str):
    """
    Добавить нового подписчика в базу данных.
    """
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO subscribers (user_id, name, phone)
                VALUES (?, ?, ?)
            """, (user_id, name, phone))


def get_subscribers():
    """
    Получить список всех подписчиков.
    """
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM subscribers WHERE subscribed = 1")
        return [row[0] for row in cur.fetchall()]


def unsubscribe(user_id: int):
    """
    Отписать пользователя от рассылки.
    """
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("UPDATE subscribers SET subscribed = 0 WHERE user_id = ?", (user_id,))


def subscribe(user_id: int):
    """
    Подписать пользователя на рассылку.
    """
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("UPDATE subscribers SET subscribed = 1 WHERE user_id = ?", (user_id,))


def check_subscription(user_id):
    """
    Проверяет, подписан ли пользователь на рассылку.
    Возвращает True, если подписан, и False, если нет.
    """
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT subscribed FROM subscribers WHERE user_id = ?", (user_id,))
        result = cur.fetchone()
        if result:
            return result[0] == 1  # Если подписка активна (subscribed = 1), то True
        return False  # Если нет записи или подписка не активна


# ================= ИНИЦИАЛИЗАЦИЯ БД =================

# Инициализируем базу данных при старте бота
init_db()
