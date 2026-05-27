import os

from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, get_user_by_email, create_user

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-spendly-change-in-prod")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    # POST: process the registration form
    name             = request.form.get("name",             "").strip()
    email            = request.form.get("email",            "").strip()
    password         = request.form.get("password",         "")
    confirm_password = request.form.get("confirm_password", "")

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
    if password != confirm_password:
        return render_template("register.html",
                               error="Passwords do not match.",
                               name=name, email=email)
    if get_user_by_email(email):
        return render_template("register.html",
                               error="An account with that email already exists.",
                               name=name, email=email)

    user_id = create_user(name, email, password)
    session["user_id"] = user_id
    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in — go straight to profile
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    # POST: authenticate
    email    = request.form.get("email",    "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("login.html",
                               error="Email and password are required.",
                               email=email)

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html",
                               error="Invalid email or password.",
                               email=email)

    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "member_since": "01 Jan 2025",
    }
    stats = {
        "total_spent": "₹12,450.75",
        "transaction_count": 8,
        "top_category": "Food",
    }
    transactions = [
        {"date": "12 Apr 2025", "description": "Groceries",            "category": "Food",          "amount": "₹850.00"},
        {"date": "11 Apr 2025", "description": "Metro card recharge",  "category": "Transport",     "amount": "₹500.00"},
        {"date": "10 Apr 2025", "description": "Electricity bill",     "category": "Bills",         "amount": "₹2,200.00"},
        {"date": "09 Apr 2025", "description": "Doctor visit",         "category": "Health",        "amount": "₹800.00"},
        {"date": "08 Apr 2025", "description": "Netflix subscription", "category": "Entertainment", "amount": "₹649.00"},
        {"date": "07 Apr 2025", "description": "New shoes",            "category": "Shopping",      "amount": "₹3,200.00"},
        {"date": "05 Apr 2025", "description": "Dinner with friends",  "category": "Food",          "amount": "₹1,450.00"},
        {"date": "01 Apr 2025", "description": "Miscellaneous",        "category": "Other",         "amount": "₹2,801.75"},
    ]
    categories = [
        {"name": "Shopping",      "amount": "₹3,200.00", "percentage": 26},
        {"name": "Other",         "amount": "₹2,801.75", "percentage": 22},
        {"name": "Food",          "amount": "₹2,300.00", "percentage": 18},
        {"name": "Bills",         "amount": "₹2,200.00", "percentage": 18},
        {"name": "Health",        "amount": "₹800.00",   "percentage":  6},
        {"name": "Entertainment", "amount": "₹649.00",   "percentage":  5},
        {"name": "Transport",     "amount": "₹500.00",   "percentage":  4},
    ]
    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
