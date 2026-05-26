from werkzeug.security import check_password_hash

from database.db import get_db


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def register(client, name="Alice Smith", email="alice@test.com",
             password="securepass", confirm_password=None):
    """Submit the registration form with the given data.
    confirm_password defaults to the same value as password (happy path)."""
    if confirm_password is None:
        confirm_password = password
    return client.post(
        "/register",
        data={
            "name": name,
            "email": email,
            "password": password,
            "confirm_password": confirm_password,
        },
    )


# ------------------------------------------------------------------ #
# Tests                                                               #
# ------------------------------------------------------------------ #

def test_register_page_loads(client):
    """GET /register returns 200 and renders the form with a confirm password field."""
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create your account" in response.data
    assert b"confirm_password" in response.data


def test_register_success(client):
    """Valid POST creates a user, sets session, and redirects to /login (302)."""
    response = client.post(
        "/register",
        data={
            "name": "Alice Smith",
            "email": "alice@test.com",
            "password": "securepass",
            "confirm_password": "securepass",
        },
        follow_redirects=False,
    )
    # Should redirect to login, not re-render the form
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    # User row should exist in the database
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", ("alice@test.com",)
    ).fetchone()
    conn.close()
    assert user is not None
    assert user["name"] == "Alice Smith"

    # session["user_id"] should be set
    with client.session_transaction() as sess:
        assert "user_id" in sess
        assert sess["user_id"] == user["id"]


def test_register_missing_name(client):
    """POST with empty name re-renders the form with the correct error."""
    response = register(client, name="")
    assert response.status_code == 200
    assert b"Name is required." in response.data


def test_register_short_password(client):
    """POST with a password shorter than 8 characters shows the length error.
    The email field should be re-populated; neither password field should appear."""
    response = register(client, email="carol@test.com", password="short",
                        confirm_password="short")
    assert response.status_code == 200
    assert b"Password must be at least 8 characters." in response.data
    # Email preserved in re-rendered form
    assert b"carol@test.com" in response.data
    # Passwords must NOT be echoed back
    assert b"short" not in response.data


def test_register_passwords_mismatch(client):
    """POST with mismatched passwords shows the mismatch error."""
    response = register(client, password="securepass", confirm_password="different1")
    assert response.status_code == 200
    assert b"Passwords do not match." in response.data


def test_register_duplicate_email(client):
    """A second registration with the same email shows the duplicate error."""
    register(client, email="dave@test.com", password="password1")
    response = register(client, name="Dave2", email="dave@test.com", password="password2")
    assert response.status_code == 200
    assert b"An account with that email already exists." in response.data


def test_register_password_not_plaintext(client):
    """After registration, the stored password_hash is not the plaintext password,
    but check_password_hash confirms it is the correct hash of that password."""
    plain = "mypassword"
    register(client, email="eve@test.com", password=plain)

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", ("eve@test.com",)
    ).fetchone()
    conn.close()
    assert user is not None
    assert user["password_hash"] != plain
    assert check_password_hash(user["password_hash"], plain) is True
