# अपना घर वृद्ध आश्रम — Django project (Milestone 1)

This is the **Milestone 1** scaffold: your existing site now runs through
Django + MySQL instead of being flat HTML files, with **no visual or
functional changes**. Nothing about auth, donors, or inventory has moved
yet — that's Milestones 2 and 3.

## What changed vs. the static site

- All 6 public pages + the admin login/dashboard now render as Django
  templates (`core/templates/`), served by real views (`core/views.py`)
  at the *same URLs* as before (`/about.html`, `/admin/login.html`, etc.)
  so nothing you bookmark or link to breaks.
- `css/`, `js/`, `images/` are now Django "static files" served via
  WhiteNoise, referenced with `{% static %}` tags instead of relative paths.
- The project is wired to MySQL via environment variables — no credentials
  are hardcoded anywhere.
- Django's own built-in admin site (for managing database rows directly,
  useful for a non-technical admin later) lives at `/django-admin/` so it
  doesn't collide with your existing `/admin/login.html`.

## What has **not** changed yet (still fake, on purpose)

- The dashboard still reads/writes `localStorage` via `admin.js` — real
  Donor/Inventory/Issue database models replace this in Milestone 3.
- The Contact form still just shows a fake success message.

## Milestone 2: real authentication

`/admin/login.html` and `/admin/dashboard.html` are now backed by real
Django auth (`django.contrib.auth`) instead of the old hardcoded JS check.
`/admin/dashboard.html` redirects anonymous visitors to `/admin/login.html`;
logging in with a real account redirects back. Logout is a POST (via the
sidebar "Logout" link) to `/admin/logout`.

Two Django Groups — **Admin** and **Volunteer** — are created automatically
by a data migration (`core/migrations/0001_create_groups.py`) the first
time you run `python manage.py migrate`. They're not assigned to anyone or
enforced anywhere yet; they exist so Milestone 3 can gate features (e.g.
only Admins can edit inventory) without another migration.

## Running it locally

### 1. Prerequisites
- Python 3.10+
- MySQL server running locally (you said you already have this ✅)

### 2. Set up a virtual environment

```bash
cd apnaghar_django
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create the MySQL database and user

In your MySQL shell:

```sql
CREATE DATABASE apnaghar_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'apnaghar_user'@'localhost' IDENTIFIED BY 'choose-a-real-password';
GRANT ALL PRIVILEGES ON apnaghar_db.* TO 'apnaghar_user'@'localhost';
FLUSH PRIVILEGES;
```

(`utf8mb4` is important — plain `utf8` in MySQL cannot store all Hindi/
Devanagari characters correctly.)

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in the real MySQL password you just set, plus a real
`DJANGO_SECRET_KEY` (any long random string — you can generate one with
`python -c "import secrets; print(secrets.token_urlsafe(50))"`).

### 5. Run migrations and start the server

```bash
python manage.py migrate
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** — it should look and behave exactly like
the static site did. Try `/about.html`, `/gallery.html`, etc. to confirm
every page and every asset (CSS, images) loads.

### 6. Create your first real admin account

`/admin/login.html` now checks against real Django accounts — there's no
hardcoded username/password anywhere anymore, so you need to create one
yourself:

```bash
python manage.py createsuperuser
```

Follow the prompts (username, email, password). Then log in at
**http://127.0.0.1:8000/admin/login.html** with that username/password —
it'll redirect you to `/admin/dashboard.html`. The same account also works
at **http://127.0.0.1:8000/django-admin/** (Django's built-in admin site),
which is mostly empty right now (no Donor/Inventory/Issue models yet — that's
Milestone 3) but is where you can add your account to the **Admin** or
**Volunteer** group under Users → (your username) → Groups, once Milestone 3
starts actually enforcing them.

## Project layout

```
apnaghar_django/
├── manage.py
├── requirements.txt
├── .env.example              # copy to .env, never commit .env
├── config/
│   ├── settings.py           # reads DB creds etc. from .env
│   ├── urls.py                # /django-admin/ + core app urls
│   └── wsgi.py / asgi.py
└── core/
    ├── views.py                # one TemplateView per page for now
    ├── urls.py                  # URLs match original filenames exactly
    ├── templates/
    │   ├── core/                 # index, about, gallery, donate, ...
    │   └── admin_panel/          # login.html, dashboard.html
    └── static/
        ├── css/style.css
        ├── js/main.js, admin.js
        └── images/*.svg
```

## If something doesn't load

- **Blank page / 500 error mentioning MySQL** — check `.env` has the right
  password and that MySQL is actually running (`mysql.server status` or
  `sudo systemctl status mysql` depending on your OS).
- **CSS/images missing** — make sure `DEBUG=True` in `.env` for local dev;
  WhiteNoise serves static files differently in debug vs. production, and
  in production you'd run `python manage.py collectstatic` first.
- **"Invalid HTTP_HOST header"** — add whatever host/port you're using to
  `DJANGO_ALLOWED_HOSTS` in `.env`.

## Next milestone (3): real Donor/Inventory/Issue data

Once you've confirmed login/logout works cleanly, next we replace the
`localStorage`-backed dashboard (`admin.js`) with real Donor, Inventory, and
Issue database models, wired through Django views/forms instead of
client-side JS.
