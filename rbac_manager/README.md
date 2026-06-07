# RBAC Manager

A Django web application implementing **Role-Based Access Control (RBAC)** with **Segregation of Duties (SoD)** enforcement and a full audit trail, built as part of MBIT 506 — Cybersecurity & Digital Forensics.

---

## Features

- **Role-based access control** — permissions are assigned to roles, roles are assigned to users
- **Least-privilege enforcement** — every resource action is gated by a permission decorator
- **Segregation of Duties** — incompatible role pairs are blocked at assignment time
- **Access attempt logging** — every allowed and denied access is recorded with a timestamp and IP address
- **Violation detection** — denied attempts auto-generate violation logs with severity ratings (LOW / MEDIUM / HIGH / CRITICAL)
- **Violation resolution workflow** — authorised staff can resolve violations with written notes
- **CSV exports** — access logs and violation reports can be exported for external review
- **Reports & analytics** — charts showing access trends, severity breakdown, top violators, and top resources
- **Modern UI** — fixed sidebar, responsive Bootstrap 5 layout, Chart.js dashboards

---

## Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- pip

### 2. Clone / extract the project

```bash
unzip rbac_manager.zip
cd rbac_manager
```

### 3. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Load demo data

This creates 7 demo users, 8 resources, 7 roles, and SoD constraints:

```bash
python manage.py setup_demo
```

### 7. Start the development server

```bash
python manage.py runserver
```

Open your browser at **http://127.0.0.1:8000/**

---

## Demo Credentials

| Username     | Password      | Role             |
|-------------|---------------|------------------|
| superadmin  | Admin@1234    | Super Admin (all access) |
| itadmin     | ITAdmin@123   | IT Admin         |
| hrmanager   | HRMgr@123     | HR Manager       |
| finmanager  | FinMgr@123    | Finance Manager  |
| finapprov   | FinApp@123    | Finance Approver |
| auditor     | Audit@123     | Auditor          |
| employee1   | Emp@12345     | Employee         |

---

## Project Structure

```
rbac_manager/
├── accounts/
│   ├── management/commands/setup_demo.py   # Demo data loader
│   ├── migrations/                          # Database migrations
│   ├── templatetags/rbac_tags.py           # Custom template filters
│   ├── admin.py                            # Django admin config
│   ├── apps.py
│   ├── context_processors.py               # Injects user permissions into all templates
│   ├── decorators.py                       # @require_permission decorator
│   ├── forms.py                            # All forms
│   ├── models.py                           # RBAC data models
│   ├── urls.py
│   └── views.py                            # All views
├── rbac_manager/
│   ├── settings.py
│   └── urls.py
├── static/css/style.css
├── templates/
│   ├── base.html
│   ├── accounts/
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   ├── profile.html
│   │   ├── reports.html
│   │   ├── logs/
│   │   │   ├── access_logs.html
│   │   │   ├── violations.html
│   │   │   └── resolve.html
│   │   ├── roles/
│   │   │   ├── list.html
│   │   │   ├── form.html
│   │   │   └── confirm_delete.html
│   │   ├── resources/
│   │   │   ├── list.html
│   │   │   └── form.html
│   │   └── users/
│   │       ├── list.html
│   │       ├── form.html
│   │       ├── detail.html
│   │       └── confirm_delete.html
├── manage.py
├── db.sqlite3
└── requirements.txt
```

---

## Creating a Superuser (optional)

If you want an additional admin account:

```bash
python manage.py createsuperuser
```

The Django admin panel is available at **http://127.0.0.1:8000/admin/**

---

## Running in Production

For production deployment, set the following in `rbac_manager/settings.py`:

```python
DEBUG = False
SECRET_KEY = 'your-new-secret-key'
ALLOWED_HOSTS = ['your-domain.com']
```

Use a production-grade database (PostgreSQL recommended) and a WSGI server such as Gunicorn behind Nginx.

---

## Assignment Reference

- Course: MBIT 506 — Cybersecurity & Digital Forensics
- Institution: Chinhoyi University of Technology (CUZ)
- Lecturer: Dr. F Masimba
- Due: 07 June 2026
