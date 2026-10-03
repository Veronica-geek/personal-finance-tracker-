# Personal Finance Tracker — Django Semester Project

Where this stands: **Phase 1 (HTML/CSS) + Phase 3 (Django Setup)** from the project checklist.
Models, admin, and a working dashboard view are in place with sample data. Forms, real
CRUD, authentication, security, the REST API, and deployment come in later phases —
don't add them yet, that's next month's work.

## What's here

- `expense_tracker/` — the Django project (settings, root urls)
- `tracker/` — the app: models (`Category`, `Transaction`, `Budget`), admin config,
  the dashboard view, and templates/CSS
- `tracker/templates/tracker/base.html` + `dashboard.html` — sidebar layout, summary
  cards, recent transactions table, budget progress bars
- `tracker/static/tracker/css/style.css` — all the styling, one file, easy to tweak
- `db.sqlite3` — a small SQLite database, pre-seeded with a few sample transactions
  and budgets so the dashboard has something to show immediately

## Running it on your own machine

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (the database is already migrated and seeded — skip to step 5.
#     Only run this if you deleted db.sqlite3 and want a fresh one)
python manage.py migrate

# 4. Create your own admin login (optional, but useful for adding data)
python manage.py createsuperuser

# 5. Run the dev server
python manage.py runserver
```

Then open `http://127.0.0.1:8000/` for the dashboard, and
`http://127.0.0.1:8000/admin/` to add/edit categories, transactions and budgets
through the Django admin.

## About the design

Rebuilt to match the "Kosten" dashboard screenshot: cream sidebar, gold
"Current Balance" card, a pink-to-purple gradient card, a dark "Top Category"
panel, a colorful 3x3 "Quick Actions" grid, small stat cards with a sparkline,
and a "Last Month Activities" table with status pills. All colors live as CSS
variables at the top of `style.css`, so retuning any of them is a one-line change.

A few pieces from the original screenshot were adapted rather than copied
literally, since they didn't map to anything in a personal finance tracker's
data model:

- **"Invoices"** → replaced with **"Top Category"**, showing your highest
  spending category this month (a real query, not decoration).
- **"Total Cashback"** → replaced with **"Total Savings"**, the sum of
  budget headroom across categories you're still under budget on.
- The **pink/purple "card"** now shows this month's income instead of a
  fictional EUR balance.
- **Quick Actions** and the bar chart's day colors are still mostly visual —
  Quick Actions will become real "add expense with this category" shortcuts
  once Forms (Phase 4) is built.

## Notes for later phases

- **Forms (Phase 4):** replace the admin-only entry with real `ModelForm`s for
  adding/editing transactions and budgets.
- **Authentication (Phase 7):** add a `user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)`
  field to `Transaction` and `Budget` (there's a reminder comment in
  `tracker/models.py`), then filter every query by `request.user`.
- **Security (Phase 8):** once auth is in, double check every view only ever
  touches the logged-in user's own data.
- **APIs (Phase 9):** Django REST Framework serializers/viewsets for
  `Transaction` and `Budget`.
- **Deployment (Phase 10):** switch `DEBUG` off, set `ALLOWED_HOSTS`, move
  `SECRET_KEY` to an environment variable before pushing to Render/Railway/etc.
