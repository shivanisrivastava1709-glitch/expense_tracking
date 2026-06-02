# Spec: Delete Expense

## Overview
Delete Expense lets a logged-in user permanently remove one of their own expense
transactions from the profile dashboard. It is the final CRUD operation in the
Spendly roadmap — registration (02), the profile dashboard (04–06), add (07), and
edit (08) are already in place, leaving delete as the last piece needed for users to
fully manage their spending history. The feature wires up the existing
`/expenses/<id>/delete` stub route, adds a single parameterised delete helper to the
database layer, and surfaces a delete control next to the existing "Edit" link in the
profile transaction table.

## Depends on
- **Step 01 — Database Setup** (`expenses` table, `get_db()` with `PRAGMA foreign_keys = ON`)
- **Step 02 — Registration / auth** (`session["user_id"]` login gate)
- **Step 05 — Profile backend routes** (`profile()` renders the transaction table)
- **Step 07 — Add Expense** (established the validation / flash / redirect-to-profile conventions)
- **Step 08 — Edit Expense** (established the `get_expense()` load + ownership-check pattern this feature reuses)

## Routes
- `POST /expenses/<int:id>/delete` — deletes the expense with the given id after an
  auth + ownership check, then redirects to the profile dashboard with a success
  flash — **logged-in only**.

> **Method change vs. the stub.** The current stub is registered as GET-only
> (`@app.route("/expenses/<int:id>/delete")`). This spec changes it to **POST**.
> Deleting on GET is unsafe — browser prefetch, link crawlers, and CSRF can trigger
> destructive deletes from a plain URL. POST keeps the same path but requires an
> actual form submission. The CLAUDE.md roadmap table lists this route as GET; that
> entry should be updated to POST when this step is marked complete.

No other new routes.

## Database changes
No schema changes. The existing `expenses` table is sufficient:

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

**One new DB helper function** is required in `database/db.py`, following the existing
`get_db()` → execute → `commit()` → `close()` pattern used by `create_expense` and
`update_expense`:

```
remove_expense(expense_id) -> None
    DELETE FROM expenses WHERE id = ?   (parameterised)
```

> **Naming — avoid a collision.** The route handler in `app.py` is already named
> `delete_expense`. To keep `app.py`'s `from database.db import (...)` block clean and
> avoid shadowing the view function, name the DB helper **`remove_expense`** (not
> `delete_expense`). Ownership is enforced in the route before this is called, so the
> helper deletes by id only.

## Templates
**Create:**
- None. Deletion is a redirect-only action; no new page is needed. (Confirmation is
  handled client-side with a vanilla-JS `confirm()` dialog — no new template, no
  separate confirmation page, consistent with steps 07/08 which added no extra pages.)

**Modify:**
- `templates/profile.html` — in the transaction table's actions cell (currently just
  the `Edit` link, `.txn-actions`), add a small inline POST form next to it:
  ```html
  <form method="POST"
        action="{{ url_for('delete_expense', id=txn.id) }}"
        onsubmit="return confirm('Delete this expense? This cannot be undone.');"
        class="txn-delete-form">
      <button type="submit" class="txn-delete">Delete</button>
  </form>
  ```
  Keep the existing `url_for('edit_expense', id=txn.id)` Edit link unchanged.

## Files to change
- `app.py` — replace the `delete_expense` stub: add `methods=["POST"]`, the auth guard,
  load via `get_expense(id)`, ownership check, call `remove_expense(id)`, flash
  `"Expense deleted."`, redirect to `profile`. Add `remove_expense` (and `get_expense`
  if not already imported) to the `from database.db import (...)` block.
- `database/db.py` — add the `remove_expense(expense_id)` helper.
- `templates/profile.html` — add the delete form/button in the actions cell.
- `static/css/profile.css` — add `.txn-delete` / `.txn-delete-form` styles.
- `CLAUDE.md` — update the route table: mark `/expenses/<id>/delete` as implemented and
  change its method to POST.

## Files to create
- None.

## New dependencies
No new dependencies. (`confirm()` is built-in browser JS — no package, no framework.)

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only.
- Parameterised queries only — `DELETE FROM expenses WHERE id = ?`, never f-strings/
  string concatenation in SQL.
- Passwords hashed with werkzeug (unchanged here — no auth/password code is touched).
- Use CSS variables — never hardcode hex values. Style `.txn-delete` with `var(--danger)`
  for its text/affordance, mirroring the `.txn-edit` rule set.
- All templates extend `base.html` (no new templates here; `profile.html` already does).
- DB logic lives in `database/db.py` only — the route must call `remove_expense()`,
  never run SQL inline.
- Auth + ownership must match the Step 08 edit pattern exactly:
  - `if not session.get("user_id"): return redirect(url_for("login"))`
  - load `expense = get_expense(id)`, then
    `if expense is None or expense["user_id"] != session["user_id"]: abort(404)`
- Use `abort()` for the not-found/forbidden case — never a bare `return "error string"`.
- Name the DB helper `remove_expense` to avoid colliding with the `delete_expense` view
  function.
- Route is **POST-only**; the delete control must be a form button, not an `<a>` link.
- Redirect to `profile` and `flash("Expense deleted.", "success")` on success, matching
  the add/edit success convention.
- All internal URLs via `url_for()` — never hardcode paths.

## Definition of done
- [ ] App starts with `python app.py` on port 5001 with no errors.
- [ ] On the profile page, each transaction row shows a **Delete** control next to **Edit**.
- [ ] Clicking **Delete** shows a browser confirm dialog; cancelling it leaves the
      expense in place.
- [ ] Confirming the delete removes that row from the table and the user lands back on
      `/profile` with a "Expense deleted." success flash.
- [ ] The profile totals / stats / category breakdown recompute correctly after a delete
      (the deleted amount is no longer counted).
- [ ] Submitting a delete for an expense id that does not exist returns **404**.
- [ ] Submitting a delete for an expense owned by a *different* user returns **404**
      (ownership enforced; no cross-user deletion).
- [ ] Visiting `/expenses/<id>/delete` via GET (e.g. typing the URL) does **not** delete
      anything — it returns 405 Method Not Allowed.
- [ ] An anonymous (logged-out) POST to the delete route redirects to `/login` and
      deletes nothing.
- [ ] No new pip packages added; `requirements.txt` unchanged.
- [ ] `database/db.py` contains a parameterised `remove_expense`; no SQL appears inline
      in `app.py`.
