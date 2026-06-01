# Spec: Edit Expense

## Overview
The Edit Expense feature lets a logged-in user modify an expense they previously created — changing its amount, category, date, or description through a pre-filled form, then persisting the update to the `expenses` table. It builds directly on Step 7 (Add Expense), which introduced the first write path into Spendly; Step 8 adds the second CRUD operation (update) and is the natural counterpart to Step 9 (delete). With edit in place, a user can correct mistakes — a wrong amount, a mis-categorised transaction — without deleting and re-adding, turning Spendly into a genuinely maintainable tracker rather than an append-only log.

## Depends on
- **Step 1 — Database setup** (`expenses` table, `get_db()` with `PRAGMA foreign_keys = ON`)
- **Step 2 — Registration** and **Login/Logout** (a valid `session["user_id"]` is required to identify the owner and authorise the edit)
- **Step 5 — Profile backend routes** (the profile page lists the user's expenses and is the redirect target after a successful edit)
- **Step 7 — Add Expense** (provides the form template, `CATEGORIES` list, `_parse_date()` helper, and the validation pattern that Step 8 mirrors; edit operates on rows this step's predecessor creates)

## Routes
- `GET /expenses/<int:id>/edit` — render the edit form pre-filled with the existing expense's values — **logged-in** (redirect to `login` if `session.get("user_id")` is missing)
- `POST /expenses/<int:id>/edit` — validate and update the expense, then redirect to `profile` with a flash confirmation — **logged-in**

> Both share the existing stub handler `edit_expense(id)` in `app.py` (currently `return "Edit expense — coming in Step 8"`, GET-only). The stub is replaced with a real `GET`/`POST` handler and its decorator updated to `methods=["GET", "POST"]`. This is the route explicitly targeted by Step 8, so implementing it is permitted by CLAUDE.md. **The Step 9 `delete_expense()` stub must remain untouched.**

**Ownership rule:** the route must load the expense via a DB helper and confirm it belongs to `session["user_id"]`. If the expense does not exist **or** belongs to another user, `abort(404)` — a user must never view or edit another user's expense.

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

**New DB helpers required** in `database/db.py` (none currently fetch a single expense or update one):

```
get_expense(expense_id) -> sqlite3.Row | None
```
- Parameterised `SELECT * FROM expenses WHERE id = ?`.
- Returns the single row (including `user_id`, so the route can check ownership) or `None` if no such id.
- Opens via `get_db()`, closes — same read pattern as `get_user_by_id`.

```
update_expense(expense_id, amount, category, date, description) -> None
```
- Parameterised `UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?`.
- Does **not** modify `user_id` or `created_at`.
- Opens via `get_db()`, commits, closes — same write pattern as `create_expense`.

> Ownership is enforced in the route (load via `get_expense`, compare `row["user_id"]` to the session user, `abort(404)` on mismatch) before `update_expense` is called — keeping the helper a simple, single-responsibility update.

## Templates
**Create:**
- `templates/edit_expense.html` — extends `base.html`; renders the expense form inside `{% block content %}`, page CSS linked via `{% block head %}`. A near-clone of `add_expense.html` with these differences: heading/subtitle reflect editing ("Edit expense" / "Update this transaction"); the `<form>` posts to `{{ url_for('edit_expense', id=expense_id) }}`; every field is pre-filled with the expense's current value (`amount`, `category`, `date`, `description`); the submit button reads **"Save changes"**; the cancel link returns to `{{ url_for('profile') }}`.

**Modify:**
- `templates/profile.html` — add an **"Edit"** link in each transaction row of the expense table, pointing to `{{ url_for('edit_expense', id=...) }}`. This is the only entry point to the feature, so each listed expense must link to its own edit page.

## Files to change
- `app.py` — replace the `edit_expense(id)` stub with a real `GET`/`POST` handler; change its decorator to `methods=["GET", "POST"]`; add `get_expense` and `update_expense` to the `from database.db import (...)` block.
- `database/db.py` — add the `get_expense()` and `update_expense()` helpers.
- `templates/profile.html` — add the per-row "Edit" link.
- `profile()` route in `app.py` — the transaction dicts built in `profile()` currently omit the expense `id`. Add `"id": row["id"]` to each transaction dict so the template can build the edit URL with `url_for('edit_expense', id=txn.id)`. (Confirm `get_expenses_by_user` selects `id`; if not, extend its `SELECT` to include `id`.)

## Files to create
- `templates/edit_expense.html` — the pre-filled edit form page.

## New dependencies
No new dependencies. Reuses Flask + `sqlite3` (already in `requirements.txt`), the standard-library date handling, and the existing `static/css/add_expense.css` for form styling — no new CSS file is required.

## Rules for implementation
- **No SQLAlchemy or ORMs** — raw `sqlite3` via `get_db()` only.
- **Parameterised queries only** — `?` placeholders in `get_expense` and `update_expense`; never f-strings or string concatenation in SQL.
- **Passwords hashed with werkzeug** — not applicable to this feature, but no auth/password handling may be weakened or bypassed.
- **Use CSS variables — never hardcode hex values** — `edit_expense.html` reuses existing classes (`.auth-section`, `.auth-card`, `.form-group`, `.form-input`, `.form-select`, `.form-textarea`, `.btn-submit`) and `add_expense.css`; if any styling is added, colours must come from the `:root` tokens in `style.css` (`--ink`, `--accent`, `--danger`, `--border`, …) — no literal hex.
- **All templates extend `base.html`** — `edit_expense.html` must `{% extends "base.html" %}` and use the existing `title` / `head` / `content` blocks.
- **DB logic stays in `database/db.py`** — the route calls `get_expense(...)` and `update_expense(...)`; no inline SQL in `app.py`.
- **Auth guard** — at the top of the handler, `if not session.get("user_id"): return redirect(url_for("login"))`, matching the `add_expense()` / `profile()` pattern.
- **Ownership check** — after loading via `get_expense(id)`: `if expense is None or expense["user_id"] != session["user_id"]: abort(404)`. Apply this on **both** GET and POST.
- **Use `abort()` for HTTP errors**, not raw string returns.
- **Use `url_for()` for every link/redirect** — including the form `action` (`url_for('edit_expense', id=expense_id)`) and the per-row profile links; no hardcoded paths.
- **Reuse the shared `CATEGORIES` constant** for the `<select>` options and server-side validation — do not redefine the category list.
- **Validation** (server-side, on POST — identical rules to Add Expense, reusing `_parse_date`):
  - `amount` required, parseable as a positive number (`> 0`); reject otherwise.
  - `category` required and must be one of `CATEGORIES` (Food, Transport, Bills, Health, Entertainment, Shopping, Other).
  - `date` required and a valid `YYYY-MM-DD` date.
  - `description` optional (stored as given, or `None` if empty).
  - On any validation failure, re-render `edit_expense.html` with an `error` message and the **submitted** values preserved (not the original DB values) — and do **not** update the row.
- **Do not touch the Step 9 delete stub** — `delete_expense()` stays a stub; only the edit route is in scope.

## Definition of done
Each item is verifiable by running the app (`python app.py`, port **5001**):

1. Visiting `/expenses/<id>/edit` while **logged out** redirects to `/login`.
2. Visiting `/expenses/<id>/edit` for an expense the logged-in user **owns** renders a form pre-filled with that expense's current amount, category (correct option selected), date, and description; the page extends `base.html` (shared navbar/footer present).
3. The category `<select>` lists exactly: Food, Transport, Bills, Health, Entertainment, Shopping, Other — with the expense's current category pre-selected.
4. Submitting **valid** changes updates that single row in `expenses` (amount/category/date/description reflect the new values; `user_id` and `created_at` unchanged), then redirects to `/profile` showing a success flash message, and the profile transaction table and stats reflect the edited values.
5. Submitting with an **empty or non-positive amount**, **missing/invalid category**, or **missing/invalid date** does **not** update the row — the form re-renders with a flash/error message and the submitted values preserved.
6. Visiting `/expenses/<id>/edit` for a **non-existent** id returns **404**.
7. Visiting `/expenses/<id>/edit` for an expense owned by a **different user** returns **404** (no data leak, no update).
8. The profile transaction table shows an **"Edit"** link on each row that links (via `url_for`) to that expense's edit page, and following it lands on the correct pre-filled form.
9. No raw SQL appears in `app.py`; the read and update go through `get_expense()` / `update_expense()` in `database/db.py` using `?` placeholders.
10. The Step 9 `delete_expense()` route is unchanged (still the stub).
