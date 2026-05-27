# ------------------------------------------------------------------ #
# Tests: /profile route (Step 04 — hardcoded UI, no DB queries)       #
# ------------------------------------------------------------------ #


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def set_session(client, user_id=1):
    """Inject a user_id into the Flask session (no real DB row needed)."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def auth_get(client, path="/profile"):
    """Set a fake session and GET the given path."""
    set_session(client)
    return client.get(path)


# ------------------------------------------------------------------ #
# Auth guard                                                          #
# ------------------------------------------------------------------ #

def test_profile_redirects_unauthenticated(client):
    """GET /profile without a session must redirect to /login."""
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_loads_for_authenticated_user(client):
    """GET /profile with a valid session must return HTTP 200."""
    response = auth_get(client)
    assert response.status_code == 200


# ------------------------------------------------------------------ #
# Stats row                                                           #
# ------------------------------------------------------------------ #

def test_profile_shows_stats(client):
    """Profile page must display total spent, transaction count, and top category."""
    response = auth_get(client)
    assert b"12,450.75" in response.data       # total_spent
    assert b"Food" in response.data            # top_category
    # transaction_count (8) is embedded in other content too; check the page renders
    assert b"8" in response.data


# ------------------------------------------------------------------ #
# Transaction table                                                   #
# ------------------------------------------------------------------ #

def test_profile_shows_transactions(client):
    """Profile page must display the hardcoded transaction rows."""
    response = auth_get(client)
    assert b"Groceries" in response.data
    assert b"Metro card recharge" in response.data
    assert b"Electricity bill" in response.data
    assert b"Entertainment" in response.data
    assert b"New shoes" in response.data
    assert b"2,801.75" in response.data        # Miscellaneous row


# ------------------------------------------------------------------ #
# Category breakdown                                                  #
# ------------------------------------------------------------------ #

def test_profile_shows_category_breakdown(client):
    """Profile page must display category breakdown rows."""
    response = auth_get(client)
    assert b"Shopping" in response.data
    assert b"Transport" in response.data
    assert b"Health" in response.data
    assert b"By Category" in response.data


# ------------------------------------------------------------------ #
# Navbar — conditional auth state                                     #
# ------------------------------------------------------------------ #

def test_navbar_shows_signout_when_authenticated(client):
    """Navbar must show 'Sign out' and hide 'Sign in' for authenticated users."""
    response = auth_get(client)
    assert b"Sign out" in response.data
    assert b"Sign in" not in response.data


def test_navbar_shows_signin_when_unauthenticated(client):
    """Navbar must show 'Sign in' and 'Get started' for guests on any page."""
    response = client.get("/")           # landing page, no session set
    assert b"Sign in" in response.data
    assert b"Get started" in response.data
    assert b"Sign out" not in response.data


# ------------------------------------------------------------------ #
# Section headings present                                            #
# ------------------------------------------------------------------ #

def test_profile_shows_section_headings(client):
    """Profile page must render both section headings."""
    response = auth_get(client)
    assert b"Recent Transactions" in response.data
    assert b"By Category" in response.data
