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


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user


def create_user(name, email, password):
    password_hash = generate_password_hash(password)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def create_expense(user_id, amount, category, date, description):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date, description),
    )
    expense_id = cur.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def get_expense(expense_id):
    conn = get_db()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    conn.close()
    return expense


def update_expense(expense_id, amount, category, date, description):
    conn = get_db()
    conn.execute(
        "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? "
        "WHERE id = ?",
        (amount, category, date, description, expense_id),
    )
    conn.commit()
    conn.close()


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


def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return user


def _date_clause(date_from, date_to):
    if date_from and date_to:
        return " AND date BETWEEN ? AND ?", (date_from, date_to)
    return "", ()


def get_expenses_by_user(user_id, date_from=None, date_to=None):
    extra_sql, extra_params = _date_clause(date_from, date_to)
    conn = get_db()
    rows = conn.execute(
        "SELECT id, amount, category, date, description "
        "FROM expenses WHERE user_id = ?"
        + extra_sql +
        " ORDER BY date DESC",
        (user_id,) + extra_params,
    ).fetchall()
    conn.close()
    return rows


def get_expense_stats(user_id, date_from=None, date_to=None):
    extra_sql, extra_params = _date_clause(date_from, date_to)
    conn = get_db()
    agg = conn.execute(
        "SELECT SUM(amount) AS total, COUNT(*) AS cnt FROM expenses WHERE user_id = ?"
        + extra_sql,
        (user_id,) + extra_params,
    ).fetchone()
    top_row = conn.execute(
        "SELECT category, SUM(amount) AS cat_total "
        "FROM expenses WHERE user_id = ?"
        + extra_sql +
        " GROUP BY category ORDER BY cat_total DESC LIMIT 1",
        (user_id,) + extra_params,
    ).fetchone()
    conn.close()
    return {
        "total_spent":       agg["total"] if agg["total"] is not None else 0.0,
        "transaction_count": agg["cnt"]   if agg["cnt"]   is not None else 0,
        "top_category":      top_row["category"] if top_row else "—",
    }


def get_category_breakdown(user_id, date_from=None, date_to=None):
    extra_sql, extra_params = _date_clause(date_from, date_to)
    conn = get_db()
    rows = conn.execute(
        "SELECT category, SUM(amount) AS total "
        "FROM expenses WHERE user_id = ?"
        + extra_sql +
        " GROUP BY category ORDER BY total DESC",
        (user_id,) + extra_params,
    ).fetchall()
    conn.close()
    return rows
