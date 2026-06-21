import sqlite3
from config import DATABASE_PATH


def get_db_connection():
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    from app.models import MODELS

    conn = get_db_connection()
    cursor = conn.cursor()
    for model in MODELS:
        cursor.execute(model.CREATE_TABLE)
        for index in model.INDEXES:
            cursor.execute(index)
    conn.commit()
    conn.close()


def fetch_all(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_one(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def execute_write(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    conn.commit()
    conn.close()


def insert_many(query, rows):
    if not rows:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executemany(query, rows)
    conn.commit()
    conn.close()
