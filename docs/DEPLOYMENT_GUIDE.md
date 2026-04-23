# Aureline Academy Production Deployment Guide

## Recommended stack
- Ubuntu 24.04 LTS VPS or cloud VM
- Docker Engine + Docker Compose plugin
- Nginx as reverse proxy
- PostgreSQL 16
- Redis 7
- SSL certificate via Let's Encrypt

## 1. Buy and point the domain
Create an `A` record for your domain or subdomain, for example `school.yourdomain.com`, and point it to your server public IP.

## 2. Prepare the server
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg nginx certbot python3-certbot-nginx
```
Install Docker using Docker's official repository, then verify `docker compose version`.

## 3. Upload the project
Copy the project folder to the server, for example to `/opt/aureline-school`.

## 4. Configure environment
```bash
cd /opt/aureline-school
cp .env.example .env
```
Set at minimum:
- `SECRET_KEY`
- `DATABASE_URL=postgresql://aureline:<strong-password>@db:5432/aureline`
- `APP_BASE_URL=https://school.yourdomain.com`
- mail settings
- WhatsApp settings if used
- Zoom settings if used
- payment portal URLs or merchant credentials

## 5. Start containers
```bash
docker compose up -d --build
```

## 6. Seed the first admin data if needed
```bash
docker compose exec web flask db upgrade
docker compose exec web flask seed-demo
```
If you do not want demo data in production, create your own admin user through a one-time shell command instead of using demo seeding.

## 7. Configure Nginx reverse proxy
Copy `deploy/nginx-aureline.conf` to `/etc/nginx/sites-available/aureline`, edit the domain, then enable it:
```bash
sudo ln -s /etc/nginx/sites-available/aureline /etc/nginx/sites-enabled/aureline
sudo nginx -t
sudo systemctl reload nginx
```

## 8. Enable SSL
```bash
sudo certbot --nginx -d school.yourdomain.com
```

## 9. Smoke test
Check:
- login page loads over HTTPS
- file uploads work
- `/admin/` loads
- `/finance/portal` works for a student user
- admin receives alert emails

## 10. Backups
At minimum back up:
- PostgreSQL database
- `instance/payment_slips/`
- `instance/profile_photos/`

## Suggested go-live checklist
- replace demo credentials
- disable demo seeding for production
- set a long random `SECRET_KEY`
- use PostgreSQL, not SQLite
- confirm HTTPS is active
- confirm mail delivery works
- confirm WhatsApp webhook works if enabled
- confirm Zoom callback URL and webhook URL are reachable
