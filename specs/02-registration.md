# Step 2 — User Registration

## Goal

Handle `POST /register` so a visitor can create a new Spendly account.  
On success the user is logged in (session set) and redirected to the landing page.  
On failure the form is re-rendered with a clear error message and the safe fields (name, email) preserved.

---

## Files to change

| File | What changes |
|---|---|
| `app.py` | Add `POST /register` handler; add `app.secret_key`; import `session`, `redirect`, `url_for`, `request`, `os` |
| `database/db.py` | Add `create_user()` and `get_user_by_email()` helpers |
| `templates/register.html` | Fix `action` attribute; preserve `name`/`email` values on re-render |

---

## 1. DB helpers — `database/db.py`

### `get_user_by_email(email)`

```python
def get_user_by_email(email):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return user          # sqlite3.Row or None
```

### `create_user(name, email, password)`

```python
def create_user(name, email, password):
    from werkzeug.security import generate_password_hash
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
```

---

## 2. Route — `app.py`

### Imports to add

```python
import os
from flask import Flask, render_template, request, redirect, url_for, session, abort
```

### Secret key (add right after `app = Flask(__name__)`)

```python
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-spendly-change-in-prod")
```

### Updated `/register` route (replace the existing GET-only stub)

```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    # --- POST: process form ---
    name     = request.form.get("name",     "").strip()
    email    = request.form.get("email",    "").strip()
    password = request.form.get("password", "")

    # Validation
    if not name:
        return render_template("register.html",
                               error="Name is required.",
                               name=name, email=email)
    if not email:
        return render_template("register.html",
                               error="Email is required.",
                               name=name, email=email)
    if len(password) < 8:
        return render_template("register.html",
                               error="Password must be at least 8 characters.",
                               name=name, email=email)

    # Duplicate-email check
    from database.db import get_user_by_email, create_user
    if get_user_by_email(email):
        return render_template("register.html",
                               error="An account with that email already exists.",
                               name=name, email=email)

    # Create account & log in
    user_id = create_user(name, email, password)
    session["user_id"] = user_id
    return redirect(url_for("landing"))
```

> **Why redirect to `landing`?**  The dashboard route is not implemented yet.
> Update this target in the step that adds the dashboard.

---

## 3. Template — `templates/register.html`

Two small changes:

1. **Fix the hardcoded `action`** — replace `action="/register"` with `action="{{ url_for('register') }}"`.
2. **Preserve field values** on error — add `value` attributes to the name and email inputs.

```html
<input type="text" id="name" name="name"
       class="form-input" placeholder="Nitish Kumar"
       value="{{ name or '' }}"
       required autofocus>

<input type="email" id="email" name="email"
       class="form-input" placeholder="nitish@example.com"
       value="{{ email or '' }}"
       required>
```

The password field intentionally has **no** `value` — never repopulate passwords.

---

## 4. Validation rules (summary)

| Field | Rule | Error message |
|---|---|---|
| `name` | Required, non-empty after strip | `"Name is required."` |
| `email` | Required, non-empty after strip | `"Email is required."` |
| `password` | At least 8 characters | `"Password must be at least 8 characters."` |
| `email` | Not already in `users` table | `"An account with that email already exists."` |

Email format is enforced by the browser (`type="email"` + `required`).  
No server-side regex needed at this step.

---

## 5. Session contract

After a successful registration, `session["user_id"]` holds the integer `id` of the
newly created row in `users`.

Later steps that protect routes will check `session.get("user_id")`.

---

## 6. Tests — `tests/test_registration.py`

Create this file. Use the `pytest-flask` fixtures (client from conftest).

| Test | Assertion |
|---|---|
| `test_register_page_loads` | `GET /register` → 200 |
| `test_register_success` | `POST` valid data → 302, `session["user_id"]` set, row in DB |
| `test_register_missing_name` | `POST` without name → 200, `b"Name is required"` in response |
| `test_register_short_password` | `POST` 7-char password → 200, error in response |
| `test_register_duplicate_email` | Second `POST` same email → 200, duplicate error in response |
| `test_register_password_hashed` | After success, `password_hash` in DB ≠ plaintext password |

### Shared `conftest.py` (create if not present)

```python
import pytest
from app import app as flask_app
from database.db import init_db

@pytest.fixture()
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    with flask_app.app_context():
        init_db()
    yield flask_app

@pytest.fixture()
def client(app):
    return app.test_client()
```

---

## 7. Out of scope for this step

- Login (`POST /login`) — Step 3  
- Logout (`GET /logout`) — Step 3  
- Dashboard / expense list — later steps  
- "Remember me" checkbox  
- Email verification  
- Password confirmation field  
