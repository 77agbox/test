import sqlite3
from contextlib import closing

from config import DB_NAME


def init_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute(
                """
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
                """
            )


def add_masterclass(data):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO masterclasses (title, place, description, teacher, date, price, link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["title"],
                    data["place"],
                    data["description"],
                    data["teacher"],
                    data["date"],
                    data["price"],
                    data["link"],
                ),
            )


def get_masterclasses():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM masterclasses")
        return cur.fetchall()


def delete_masterclass(mc_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("DELETE FROM masterclasses WHERE id = ?", (mc_id,))
