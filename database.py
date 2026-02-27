import sqlite3
from contextlib import closing

DB_NAME = "masterclasses.db"


def init_db():
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
                    link TEXT,
                    active INTEGER DEFAULT 1
                )
            """)


def add_masterclass(data: dict):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("""
                INSERT INTO masterclasses
                (title, place, description, teacher, date, price, link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data["title"],
                data["place"],
                data["description"],
                data["teacher"],
                data["date"],
                data["price"],
                data["link"],
            ))


def get_masterclasses():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM masterclasses WHERE active=1")
        return cur.fetchall()


def delete_masterclass(mc_id: int):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute(
                "UPDATE masterclasses SET active=0 WHERE id=?",
                (mc_id,)
            )
