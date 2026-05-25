import os
import sqlite3
from werkzeug.security import generate_password_hash

_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "spendly.db"
)


def get_db():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()

    # Guard: skip if any users already exist
    row = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
    if row["cnt"] > 0:
        conn.close()
        return

    # Insert demo user
    password_hash = generate_password_hash("demo123")
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )
    user_id = cur.lastrowid

    # Insert 8 sample expenses covering all 7 categories
    expenses = [
        (user_id,  12.50, "Food",          "2026-05-01", "Lunch at canteen"),
        (user_id,  45.00, "Transport",     "2026-05-03", "Monthly bus pass top-up"),
        (user_id, 120.00, "Bills",         "2026-05-07", "Electricity bill"),
        (user_id,  30.00, "Health",        "2026-05-10", "Pharmacy"),
        (user_id,  18.75, "Entertainment", "2026-05-13", "Movie ticket"),
        (user_id,  65.00, "Shopping",      "2026-05-17", "New t-shirt"),
        (user_id,   9.99, "Other",         "2026-05-20", "Umbrella"),
        (user_id,  22.00, "Food",          "2026-05-23", "Dinner with friends"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )

    conn.commit()
    conn.close()
