import os
from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from werkzeug.security import check_password_hash
from database.db import (
    get_db, init_db, seed_db, get_user_by_email, create_user,
    get_user_by_id, get_expenses_by_user, get_expense_stats, get_category_breakdown,
    create_expense,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-spendly-change-in-prod")

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


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


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _months_ago(today, n):
    m, y = today.month - n, today.year
    if m <= 0:
        m += 12
        y -= 1
    try:
        return date(y, m, today.day)
    except ValueError:
        return date(y, m, 1)


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # --- Parse and validate date filter params ---
    date_from = _parse_date(request.args.get("date_from", ""))
    date_to   = _parse_date(request.args.get("date_to",   ""))
    if date_from and date_to and date_from > date_to:
        flash("Start date must be before end date.", "error")
        date_from = date_to = None
    df_str = date_from.strftime("%Y-%m-%d") if date_from else None
    dt_str = date_to.strftime("%Y-%m-%d")   if date_to   else None

    # --- Preset date ranges ---
    today = date.today()
    preset_this_month = {
        "date_from": today.replace(day=1).strftime("%Y-%m-%d"),
        "date_to":   today.strftime("%Y-%m-%d"),
    }
    preset_last_3 = {
        "date_from": _months_ago(today, 3).strftime("%Y-%m-%d"),
        "date_to":   today.strftime("%Y-%m-%d"),
    }
    preset_last_6 = {
        "date_from": _months_ago(today, 6).strftime("%Y-%m-%d"),
        "date_to":   today.strftime("%Y-%m-%d"),
    }

    # --- Determine active filter token ---
    if df_str is None and dt_str is None:
        active_filter = "all"
    elif df_str == preset_this_month["date_from"] and dt_str == preset_this_month["date_to"]:
        active_filter = "this_month"
    elif df_str == preset_last_3["date_from"] and dt_str == preset_last_3["date_to"]:
        active_filter = "last_3"
    elif df_str == preset_last_6["date_from"] and dt_str == preset_last_6["date_to"]:
        active_filter = "last_6"
    else:
        active_filter = "custom"

    # --- User block ---
    db_user = get_user_by_id(user_id)
    if db_user is None:
        abort(404)
    member_since = datetime.strptime(db_user["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")
    user = {
        "name": db_user["name"],
        "email": db_user["email"],
        "member_since": member_since,
    }

    # --- Transaction history ---
    transactions = [
        {
            "date":        datetime.strptime(row["date"], "%Y-%m-%d").strftime("%d %b %Y"),
            "description": row["description"] or "",
            "category":    row["category"],
            "amount":      f"₹{row['amount']:,.2f}",
        }
        for row in get_expenses_by_user(user_id, date_from=df_str, date_to=dt_str)
    ]

    # --- Summary stats ---
    raw_stats = get_expense_stats(user_id, date_from=df_str, date_to=dt_str)
    stats = {
        "total_spent":       f"₹{raw_stats['total_spent']:,.2f}",
        "transaction_count": raw_stats["transaction_count"],
        "top_category":      raw_stats["top_category"],
    }

    # --- Category breakdown ---
    raw_categories = get_category_breakdown(user_id, date_from=df_str, date_to=dt_str)
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
        active_filter=active_filter,
        date_from=df_str or "",
        date_to=dt_str or "",
        preset_this_month=preset_this_month,
        preset_last_3=preset_last_3,
        preset_last_6=preset_last_6,
    )


@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("analytics.html")


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    user_id = session["user_id"]
    today = date.today().strftime("%Y-%m-%d")

    if request.method == "GET":
        return render_template("add_expense.html", categories=CATEGORIES, today=today)

    # POST: read and strip submitted values
    amount_raw  = request.form.get("amount",      "").strip()
    category    = request.form.get("category",    "").strip()
    date_raw    = request.form.get("date",        "").strip()
    description = request.form.get("description", "").strip()

    def _reshow(error):
        return render_template("add_expense.html", categories=CATEGORIES, today=today,
                               error=error, amount=amount_raw, category=category,
                               date=date_raw, description=description)

    try:
        amount = float(amount_raw)
    except ValueError:
        return _reshow("Amount must be a number.")
    if amount <= 0:
        return _reshow("Amount must be greater than zero.")
    if category not in CATEGORIES:
        return _reshow("Please choose a valid category.")
    parsed = _parse_date(date_raw)
    if parsed is None:
        return _reshow("Please enter a valid date.")

    create_expense(user_id, round(amount, 2), category,
                   parsed.strftime("%Y-%m-%d"), description or None)
    flash("Expense added.", "success")
    return redirect(url_for("profile"))


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
