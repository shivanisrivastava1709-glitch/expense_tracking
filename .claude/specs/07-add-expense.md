# Spec: Add Expense

## Overview
The Add Expense feature lets a logged-in user record a new expense through a dedicated form (amount, category, date, optional description) and persists it to the `expenses` table. This is the first feature in the Spendly roadmap that *writes* expense data — every prior step (registration, login, profile dashboard, date filtering, analytics) only read or displayed seeded data. Implementing step 7 turns Spendly from a read-only demo into a usable tracker: the profile dashboard and category breakdown finally reflect data the user entered themselves. It also unblocks steps 8 (edit) and 9 (delete), which operate on rows this feature creates.

## Depends on
- **Step 1 — Database setup** (`expenses` table, `get_db()` with `PRAGMA foreign_keys = ON`)
- **Step 2 — Registration** and **Login/Logout** (a valid `session["user_id"]` must exist to attribute the expense to a user)
- **Step 5 — Profile backend routes** (the profile page is where new expenses appear after creation; it is also the natural redirect target)

## Routes
- `GET /expenses/add` — render the add-expense form — **logged-in** (redirect to `login` if `session.get("user_id")` is missing)
- `POST /expenses/add` — validate and insert the new expense, then redirect to `profile` with a flash confirmation — **logged-in**

> Both share the existing stub handler `add_expense()` in `app.py` (currently returns a raw string). The stub is replaced with a real GET/POST handler. This is the route explicitly targeted by step 7, so implementing it is permitted by CLAUDE.md.

## Database changes
No schema changes. The `expenses` table already has every needed column:

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL,
    date        TEXT    NOT NULL,
    description TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
)
```

**New DB helper required** in `database/db.py` (no helper currently inserts expenses):

```
create_expense(user_id, amount, category, date, description) -> int
```
- Parameterised `INSERT` only.
- Returns the new expense id (`cursor.lastrowid`).
- Opens via `get_db()`, commits, closes — same pattern as `create_user`.

## Templates
**Create:**
- `templates/add_expense.html` — extends `base.html`; renders the expense form inside `{% block content %}`, page CSS linked via `{% block head %}`. Mirrors the structure of `register.html` / `login.html` (form card, `.form-group`, error display, `.btn-submit`).

**Modify:**
- `templates/profile.html` — add an **"Add Expense"** link/button (styled `.btn-primary`) near the page heading, pointing to `{{ url_for('add_expense') }}`. This is the only entry point to the feature, so the profile page must link to it.

## Files to change
- `app.py` — replace the `add_expense()` stub with a real `GET`/`POST` handler; add `create_expense` to the `from database.db import (...)` block.
- `database/db.py` — add the `create_expense()` helper.
- `templates/profile.html` — add the "Add Expense" button.

## Files to create
- `templates/add_expense.html` — the form page.
- `static/css/add_expense.css` — page-specific styles for the form (only if `style.css` form classes are insufficient; reuse existing `.form-group` / `.form-input` / `.btn-submit` where possible).

## New dependencies
No new dependencies. Date handling uses the standard library; rendering and persistence use Flask + sqlite3 already in `requirements.txt`.

## Rules for implementation
- **No SQLAlchemy or ORMs** — raw `sqlite3` via `get_db()` only.
- **Parameterised queries only** — `?` placeholders in `create_expense`; never f-strings or string concatenation in SQL.
- **Passwords hashed with werkzeug** — not applicable to this feature, but no auth/password handling may be weakened or bypassed.
- **Use CSS variables — never hardcode hex values** — all colors from the `:root` tokens in `style.css` (`--ink`, `--accent`, `--danger`, `--border`, etc.). No literal hex in `add_expense.css`.
- **All templates extend `base.html`** — `add_expense.html` must `{% extends "base.html" %}` and use the existing `title` / `head` / `content` blocks.
- **DB logic stays in `database/db.py`** — the route calls `create_expense(...)`; no inline SQL in `app.py`.
- **Auth guard** — at the top of the handler, `if not session.get("user_id"): return redirect(url_for("login"))`, matching the `profile()` / `analytics()` pattern.
- **Use `url_for()` for every link/redirect** — no hardcoded paths.
- **Use `abort()` for HTTP errors**, not raw string returns.
- **Validation** (server-side, on POST):
  - `amount` required, parseable as a positive number (`> 0`); reject otherwise.
  - `category` required and must be one of the known categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other.
  - `date` required and a valid `YYYY-MM-DD` date.
  - `description` optional (may be empty / stored as given).
  - On any validation failure, `flash()` a clear message and re-render `add_expense.html` (preserving entered values) rather than inserting.
- **Category list** should be defined once and shared between the template `<select>` and the server-side validation (e.g. passed into the template context) to avoid drift.

## Definition of done
Each item is verifiable by running the app (`python app.py`, port **5001**):

1. Visiting `/expenses/add` while **logged out** redirects to `/login`.
2. Visiting `/expenses/add` while **logged in** renders a form with fields: amount, category (dropdown of the 7 categories), date, and description — and the page extends `base.html` (shared navbar/footer present).
3. The form's category `<select>` lists exactly: Food, Transport, Bills, Health, Entertainment, Shopping, Other.
4. Submitting a **valid** expense inserts one row into `expenses` with the correct `user_id` (the logged-in user), `amount`, `category`, `date`, and `description`, then redirects to `/profile` showing a success flash message.
5. The newly added expense is visible in the profile transaction table and is reflected in the stats cards / category breakdown (totals and counts increase accordingly).
6. Submitting with **empty or non-positive amount**, **missing/invalid category**, or **missing/invalid date** does **not** insert a row — the form re-renders with a flash error and previously entered values preserved.
7. The profile page shows an **"Add Expense"** button that links (via `url_for`) to `/expenses/add`.
8. No raw SQL appears in `app.py`; the insert goes through `create_expense()` in `database/db.py` using `?` placeholders.
9. `add_expense.css` (if created) contains no hardcoded hex color values — only `var(--…)` references.
