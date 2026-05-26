# Spec: Registration

## Overview

This step wires up the `POST /register` handler so a new visitor can create a Spendly account. The form already exists (`register.html`) but the route is GET-only and does nothing with submitted data. Completing this step closes that gap: the server validates the submitted name, email, password, and confirm password; rejects mismatched passwords, duplicates, and weak passwords with a clear error message; hashes the password with werkzeug; inserts the new user into the `users` table; sets `session["user_id"]`; and redirects to the login page so the user can sign in. This is the first step that introduces Flask sessions, making it the prerequisite for every subsequent authenticated route (profile, expenses, logout).

---

## Depends on

- **Step 1 — Database Setup**: `get_db()`, `init_db()`, `seed_db()`, and the `users` table must already exist in `database/db.py`.

---

## Routes

- `POST /register` — Receive and process the registration form — **public**

The existing `GET /register` handler is extended to also accept `POST`; it is not replaced.

---

## Database changes

No new tables or columns needed. The `users` table created in Step 1 already has every required column:

| Column | Used by this step |
|---|---|
| `name` | Stored from form field |
| `email` | Stored; UNIQUE constraint prevents duplicates |
| `password_hash` | Stored as werkzeug hash of submitted password |
| `created_at` | Auto-filled by SQLite default |

---

## Templates

**Modify** — `templates/register.html`:
- Change `action="/register"` → `action="{{ url_for('register') }}"`
- Add `value="{{ name or '' }}"` to the name `<input>`
- Add `value="{{ email or '' }}"` to the email `<input>`
- Add a **Confirm password** `<input type="password">` field (name=`confirm_password`) after the password field
- Neither password field should be repopulated on error (intentional)

**Create** — none.

---

## Files to change

- `app.py` — add `POST /register` logic; add `app.secret_key`; extend imports
- `database/db.py` — add `get_user_by_email()` and `create_user()` helpers
- `templates/register.html` — fix action URL; add confirm password field; preserve name/email on re-render

---

## Files to create

- `tests/test_registration.py` — pytest test suite for this step
- `tests/conftest.py` — shared `app` and `client` fixtures (create only if not present)

---

## New dependencies

No new pip packages. `werkzeug.security` is already available via `werkzeug==3.1.6`.

---

## Rules for implementation

- No SQLAlchemy or ORMs — use raw `sqlite3` only
- Parameterised queries only — never f-strings or string concatenation in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash()` — never stored plaintext
- Use CSS variables — never hardcode hex colour values in any template or stylesheet
- All templates must extend `base.html`
- `app.secret_key` must be set before any `session` usage — read from `os.environ.get("SECRET_KEY", "dev-secret-spendly-change-in-prod")`
- DB helpers live in `database/db.py` — no SQL inside route functions in `app.py`
- Use `abort()` for unexpected server-side errors, not bare string returns
- Redirect after successful POST using `redirect(url_for(...))` — never re-render on success

### New helpers required in `database/db.py`

**`get_user_by_email(email)`**
- Queries `users` table by email
- Returns a `sqlite3.Row` if found, `None` otherwise

**`create_user(name, email, password)`**
- Hashes `password` with `generate_password_hash()`
- Inserts into `users`
- Returns the new `user_id` (integer)

### Imports to add to `app.py`

```python
import os
from flask import Flask, render_template, request, redirect, url_for, session, abort
from database.db import get_db, init_db, seed_db, get_user_by_email, create_user
```

### Validation order in `POST /register`

1. `name` is non-empty after `.strip()`
2. `email` is non-empty after `.strip()`
3. `password` is at least 8 characters
4. `password` equals `confirm_password`
5. `get_user_by_email(email)` returns `None` (no duplicate)

Return a 200 with `error=` and safe field values (`name`, `email` only — never passwords) on any failure. Redirect on success.

### Error messages (exact strings)

| Failure | Message |
|---|---|
| Missing name | `"Name is required."` |
| Missing email | `"Email is required."` |
| Password < 8 chars | `"Password must be at least 8 characters."` |
| Passwords don't match | `"Passwords do not match."` |
| Email taken | `"An account with that email already exists."` |

### Success redirect

After creating the user and setting `session["user_id"]`, redirect to **`url_for("login")`** so the user signs in with their new credentials.

---

## Definition of done

- [ ] `GET /register` returns 200 and renders the form with a confirm password field
- [ ] Submitting the form with valid data creates a new row in `users` with a hashed password (not plaintext)
- [ ] After successful registration, `session["user_id"]` is set to the new user's id
- [ ] Successful registration redirects to the login page (HTTP 302)
- [ ] Submitting with an empty name re-renders the form with `"Name is required."` visible
- [ ] Submitting with a password shorter than 8 characters re-renders the form with the correct error
- [ ] Submitting mismatched passwords re-renders the form with `"Passwords do not match."`
- [ ] Submitting a duplicate email re-renders the form with `"An account with that email already exists."`
- [ ] On error, the name and email fields are re-populated; neither password field is repopulated
- [ ] All tests in `tests/test_registration.py` pass with `pytest`
