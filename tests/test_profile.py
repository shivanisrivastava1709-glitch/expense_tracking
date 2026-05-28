# ------------------------------------------------------------------ #
# Tests: /profile route (Step 05 — live DB queries)                   #
# ------------------------------------------------------------------ #

from database.db import get_db, create_user


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def seed_profile_user(app):
    """Insert a test user + 3 expenses; return the user_id."""
    with app.app_context():
        uid = create_user("Test User", "test@spendly.com", "testpass123")
        conn = get_db()
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            [
                (uid, 850.00,  "Food",      "2026-04-12", "Groceries"),
                (uid, 500.00,  "Transport", "2026-04-11", "Metro card recharge"),
                (uid, 2200.00, "Bills",     "2026-04-10", "Electricity bill"),
            ],
        )
        conn.commit()
        conn.close()
    return uid


def auth_get(client, user_id, path="/profile"):
    """Inject a real user_id into the session and GET the given path."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
    return client.get(path)


# ------------------------------------------------------------------ #
# Auth guard                                                          #
# ------------------------------------------------------------------ #

def test_profile_redirects_unauthenticated(client):
    """GET /profile without a session must redirect to /login."""
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_loads_for_authenticated_user(client, app):
    """GET /profile with a valid session must return HTTP 200."""
    uid = seed_profile_user(app)
    response = auth_get(client, uid)
    assert response.status_code == 200


# ------------------------------------------------------------------ #
# Stats row                                                           #
# ------------------------------------------------------------------ #

def test_profile_shows_stats(client, app):
    """Profile page must display live total spent, transaction count, and top category."""
    uid = seed_profile_user(app)
    response = auth_get(client, uid)
    assert response.status_code == 200
    assert b"3,550.00" in response.data    # 850 + 500 + 2200
    assert b"Bills" in response.data       # top category by sum
    assert b"3" in response.data           # transaction_count


# ------------------------------------------------------------------ #
# Transaction table                                                   #
# ------------------------------------------------------------------ #

def test_profile_shows_transactions(client, app):
    """Profile page must display the seeded transaction rows from the DB."""
    uid = seed_profile_user(app)
    response = auth_get(client, uid)
    assert b"Groceries" in response.data
    assert b"Metro card recharge" in response.data
    assert b"Electricity bill" in response.data


# ------------------------------------------------------------------ #
# Category breakdown                                                  #
# ------------------------------------------------------------------ #

def test_profile_shows_category_breakdown(client, app):
    """Profile page must display category breakdown rows from the DB."""
    uid = seed_profile_user(app)
    response = auth_get(client, uid)
    assert b"Bills" in response.data
    assert b"Food" in response.data
    assert b"Transport" in response.data
    assert b"By Category" in response.data


# ------------------------------------------------------------------ #
# Zero-expenses edge case                                             #
# ------------------------------------------------------------------ #

def test_profile_zero_expenses(client, app):
    """A user with no expenses must see ₹0.00, 0 transactions, and — for top category."""
    with app.app_context():
        uid = create_user("Empty User", "empty@spendly.com", "testpass123")
    with client.session_transaction() as sess:
        sess["user_id"] = uid
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"0.00" in response.data
    assert "—".encode() in response.data


# ------------------------------------------------------------------ #
# Navbar — conditional auth state                                     #
# ------------------------------------------------------------------ #

def test_navbar_shows_signout_when_authenticated(client, app):
    """Navbar must show 'Sign out' and hide 'Sign in' for authenticated users."""
    uid = seed_profile_user(app)
    response = auth_get(client, uid)
    assert b"Sign out" in response.data
    assert b"Sign in" not in response.data


def test_navbar_shows_signin_when_unauthenticated(client):
    """Navbar must show 'Sign in' and 'Get started' for guests on any page."""
    response = client.get("/")
    assert b"Sign in" in response.data
    assert b"Get started" in response.data
    assert b"Sign out" not in response.data


# ------------------------------------------------------------------ #
# Section headings present                                            #
# ------------------------------------------------------------------ #

def test_profile_shows_section_headings(client, app):
    """Profile page must render both section headings."""
    uid = seed_profile_user(app)
    response = auth_get(client, uid)
    assert b"Recent Transactions" in response.data
    assert b"By Category" in response.data
