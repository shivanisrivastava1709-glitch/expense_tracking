import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import check_password_hash
from database.db import (
    get_db, init_db, seed_db, get_user_by_email, create_user,
    get_user_by_id, get_expenses_by_user, get_expense_stats, get_category_breakdown,
)

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

    user_id = session["user_id"]

    # --- AGENT-0: user block ---
    db_user = get_user_by_id(user_id)
    if db_user is None:
        abort(404)
    member_since = datetime.strptime(db_user["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")
    user = {
        "name": db_user["name"],
        "email": db_user["email"],
        "member_since": member_since,
    }

    # --- AGENT-1: transaction history ---
    transactions = [
        {
            "date":        datetime.strptime(row["date"], "%Y-%m-%d").strftime("%d %b %Y"),
            "description": row["description"] or "",
            "category":    row["category"],
            "amount":      f"₹{row['amount']:,.2f}",
        }
        for row in get_expenses_by_user(user_id)
    ]

    # --- AGENT-2: summary stats ---
    raw_stats = get_expense_stats(user_id)
    stats = {
        "total_spent":       f"₹{raw_stats['total_spent']:,.2f}",
        "transaction_count": raw_stats["transaction_count"],
        "top_category":      raw_stats["top_category"],
    }

    # --- AGENT-3: category breakdown ---
    raw_categories = get_category_breakdown(user_id)
    grand_total = sum(row["total"] for row in raw_categories)
    categories = [
        {
            "name":       row["category"],
            "amount":     f"₹{row['total']:,.2f}",
            "percentage": round(row["total"] / grand_total * 100) if grand_total else 0,
        }
        for row in raw_categories
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
