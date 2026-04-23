# Installation Guide

## Local setup
1. Copy `.env.example` to `.env`.
2. Create and activate a virtual environment.
3. Install requirements.
4. Run migrations.
5. Seed demo users.
6. Start the Flask server.

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

If the migrations folder is missing in a fresh clone, initialize once:

```bash
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

## Default login credentials
- Admin: `admin@aureline.edu` / `admin123`
- Teacher: `teacher@aureline.edu` / `teacher123`
- Student: `student@aureline.edu` / `student123`
- Parent: `parent@aureline.edu` / `parent123`

## Production notes
- Set a strong `SECRET_KEY`.
- Use PostgreSQL or MySQL in production.
- Put Gunicorn behind Nginx or a cloud load balancer.
- Configure HTTPS before enabling WhatsApp, Messenger, or Zoom callbacks.


## Docker setup

```bash
docker compose up --build
```

The Docker Compose setup points the web container at PostgreSQL and runs `flask db upgrade` before starting Gunicorn.
