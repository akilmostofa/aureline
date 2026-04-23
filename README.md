<<<<<<< HEAD
# aureline
aureline academy
=======
# Aureline Academy School Management System

A modular Flask-based **full CRUD** school management application for Aureline Academy with:

- role-based login for admin, teacher, and student users
- public registration for **student** accounts only; teacher creation stays admin-only
- CRUD interfaces for students, teachers, courses, attendance, invoices, library books, and notices
- course selection and fee submission with **live cart total**
- **PDF payment slip upload** for course payment requests
- automatic **email / WhatsApp admin alerts** on new payment requests when credentials are configured
- Flask-Migrate database migrations
- seeded demo users and sample records
- a working Flask-Admin admin panel at `/admin`
- reporting dashboard
- Zoom / payment / chatbot integration scaffolding
- responsive Bootstrap UI and PWA manifest/service worker

## Quick start

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=run.py
flask db upgrade
flask seed-demo
python run.py
```

## Demo users

## Main routes

- `/` public landing page
- `/auth/login` login
- `/auth/register` registration request
- `/dashboard/` application dashboard
- `/students/` students CRUD
- `/teachers/` teachers CRUD
- `/courses/` courses CRUD
- `/attendance/` attendance CRUD
- `/finance/` invoice CRUD
- `/finance/portal` student course selection and payment portal
- `/finance/requests` admin review for course payment requests
- `/admin/` Flask-Admin panel
- `/chatbot/*` chatbot endpoints
- `/integrations/zoom/*` Zoom scaffolding

## Payment request flow

1. Admin sets **course fees** and enrollment status in Courses.
2. Student chooses course(s) from `/finance/portal`.
3. Student sees a **live cart total**, enters payment details, and uploads the **payment slip as PDF**.
4. The app stores the request as **pending** and sends email / WhatsApp alerts to Aureline Admin if configured.
5. Admin reviews the request at `/finance/requests` or `/admin`.
6. Admin approves or rejects the request within 24 hours.
7. On approval, paid invoice records are created automatically.

## Environment variables for alerts

- `ADMIN_ALERT_EMAIL`
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
- `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `AURELINE_NOTIFY_WHATSAPP`

## Notes

- The payment service and Zoom service are secure scaffolds and still need merchant/API credentials for production.
- Replace the placeholder logo SVG with Aureline Academy’s official logo file when available.
- SQLite is the default for local setup; switch `DATABASE_URL` for PostgreSQL/MySQL in production.
- Uploaded payment slips are stored under the Flask `instance/` folder.


## Production deployment and live integrations

See `docs/DEPLOYMENT_GUIDE.md`, `docs/ZOOM_LIVE_SETUP.md`, and `docs/PAYMENT_LIVE_SETUP.md`.
>>>>>>> 082c104 (Initial commit)
