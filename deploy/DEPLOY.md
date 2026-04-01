# GB Golf Optimizer -- VPS Deployment Guide

Target: Hostinger KVM 2 VPS (193.46.198.60)
User: deploy
App path: /opt/GBGolfOptimizer
URL: https://gameblazers.silverreyes.net/golf

---

## 1. Prerequisites

The following must already be present on the VPS:

- Python >= 3.10 (`python3 --version`)
- Docker running with a PostgreSQL 16 container (shared with nflpredictor)
- Nginx installed and running
- `deploy` user with sudo access and membership in the `docker` group
- DNS A record for `gameblazers.silverreyes.net` pointing to 193.46.198.60

---

## 2. PostgreSQL Setup (one-time)

Create the `gbgolf` database and user inside the existing Docker PostgreSQL container.

```bash
# Discover the PostgreSQL container name
docker ps --filter "ancestor=postgres" --format "table {{.Names}}\t{{.Status}}"

# Create user and database (substitute CONTAINER_NAME from above)
docker exec -i CONTAINER_NAME psql -U postgres <<'SQL'
CREATE USER gbgolf WITH PASSWORD 'CHANGEME';
CREATE DATABASE gbgolf OWNER gbgolf;
GRANT ALL PRIVILEGES ON DATABASE gbgolf TO gbgolf;
SQL

# Verify the database was created
docker exec -i CONTAINER_NAME psql -U postgres -c "\l" | grep gbgolf
```

**Note:** Replace `CONTAINER_NAME` with the actual name from `docker ps`. Replace `CHANGEME` with a secure password.

---

## 3. Environment Variables (one-time)

Create the `.env` file on the VPS:

```bash
cat > /opt/GBGolfOptimizer/.env << 'EOF'
DATABASE_URL=postgresql://gbgolf:CHANGEME@localhost:5432/gbgolf
DATAGOLF_API_KEY=your-actual-api-key
SECRET_KEY=generate-a-random-string-here
FLASK_APP=gbgolf.web:create_app
EOF
chmod 600 /opt/GBGolfOptimizer/.env
```

**Note:** Replace `CHANGEME` with the password from Step 2. Replace the API key with your DataGolf Scratch Plus key (from datagolf.com account). Replace the secret key with a random string (e.g. `python3 -c "import secrets; print(secrets.token_hex(32))"`). The `.env` file is in `.gitignore` and is NOT synced by `deploy.sh`.

---

## 4. Initial Setup (one-time)

```bash
# Create virtual environment
cd /opt/GBGolfOptimizer
python3 -m venv .venv
.venv/bin/pip install -e .

# Create logs directory for cron
mkdir -p /opt/GBGolfOptimizer/logs
```

---

## 5. Deploy Code

From your local machine:

```bash
bash deploy/deploy.sh
```

`deploy.sh` performs three steps:

1. **Sync files** -- creates a tar archive of the project (excluding `.git`, `.planning`, `__pycache__`, `.venv`, and socket files) and extracts it on the VPS via SSH.
2. **Run database migration** -- executes `flask db upgrade` on the VPS to apply any pending schema changes. This is idempotent and safe to run on every deploy.
3. **Restart service** -- restarts the `gbgolf` systemd service and prints its status.

The deploy script is idempotent and safe to run repeatedly.

---

## 6. Systemd Service

The service file with real values:

```ini
[Unit]
Description=GB Golf Optimizer (Gunicorn)
After=network.target

[Service]
User=deploy
Group=www-data
WorkingDirectory=/opt/GBGolfOptimizer
Environment="PATH=/opt/GBGolfOptimizer/.venv/bin"
Environment="SCRIPT_NAME=/golf"
ExecStart=/opt/GBGolfOptimizer/.venv/bin/gunicorn \
    --workers 2 \
    --bind unix:/opt/GBGolfOptimizer/gbgolf.sock \
    --umask 007 \
    wsgi:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Worker count (2) matches the 2 vCPUs on the Hostinger KVM 2.

Installation:

```bash
sudo cp deploy/gbgolf.service /etc/systemd/system/gbgolf.service
sudo systemctl daemon-reload
sudo systemctl enable gbgolf
sudo systemctl start gbgolf
sudo systemctl status gbgolf
```

Look for `active (running)`. If it shows `failed`, check `sudo journalctl -u gbgolf -n 50`.

---

## 7. Nginx Configuration

The Nginx config with the real socket path:

```nginx
server {
    listen 80;
    server_name gameblazers.silverreyes.net;

    location /golf {
        include proxy_params;
        proxy_pass http://unix:/opt/GBGolfOptimizer/gbgolf.sock;
        proxy_set_header X-Forwarded-Prefix /golf;
    }
}
```

Installation:

```bash
sudo cp deploy/gameblazers.silverreyes.net.nginx /etc/nginx/sites-available/gameblazers.silverreyes.net
sudo ln -s /etc/nginx/sites-available/gameblazers.silverreyes.net /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

**Note:** After Nginx is serving HTTP, run `sudo certbot --nginx -d gameblazers.silverreyes.net` for HTTPS.

---

## 8. Cron Setup (one-time)

```bash
# Check VPS timezone
timedatectl

# Edit crontab for the deploy user (NOT root)
crontab -e

# Every 2 hours, 10am–10pm EDT, Tuesday and Wednesday only.
# 8pm and 10pm EDT cross midnight UTC, so they run on Wed/Thu UTC.
# 10am–6pm EDT = 14–22 UTC same day (Tue/Wed)
0 14,16,18,20,22 * * 2,3 cd /opt/GBGolfOptimizer && FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections >> logs/fetch.log 2>&1
# 8pm EDT = 00:00 UTC next day (Wed/Thu)
0 0 * * 3,4 cd /opt/GBGolfOptimizer && FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections >> logs/fetch.log 2>&1
# 10pm EDT = 02:00 UTC next day (Wed/Thu)
0 2 * * 3,4 cd /opt/GBGolfOptimizer && FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections >> logs/fetch.log 2>&1
```

**Notes:**
- 14 fetches per week: 7 per day on Tue and Wed (10am, 12pm, 2pm, 4pm, 6pm, 8pm, 10pm EDT)
- Fetching frequently is safe — the command is idempotent (replaces stale data cleanly)
- Run as the `deploy` user, NOT root
- The `logs/` directory must exist (created in Step 4)
- `FLASK_APP` is required because cron runs with a minimal environment; once `create_app()` runs, `load_dotenv()` picks up `DATABASE_URL` and `DATAGOLF_API_KEY` from `.env`

---

## 9. Verification Checklist

```bash
# 1. Manually run the fetcher
cd /opt/GBGolfOptimizer
FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections

# 2. Check the fetch log
cat logs/fetch.log
# Expected: "OK | {Tournament Name} | {N} players | fetch_id={N}"

# 3. Check database rows
docker exec -i CONTAINER_NAME psql -U gbgolf -d gbgolf -c "SELECT id, tournament_name, player_count, fetched_at FROM fetches ORDER BY fetched_at DESC LIMIT 5;"

# 4. Check projection count (should be >= 30)
docker exec -i CONTAINER_NAME psql -U gbgolf -d gbgolf -c "SELECT COUNT(*) FROM projections;"

# 5. Browser verification
# Open https://gameblazers.silverreyes.net/golf
# - Select "DataGolf" source: verify staleness label shows tournament name + relative age
# - Upload roster CSV, click Optimize: verify lineups appear
# - Select "Upload CSV" source: verify file upload still works correctly
```

---

## 10. Quick Reference

```bash
# Service status
sudo systemctl status gbgolf

# Restart after deploy
sudo systemctl restart gbgolf

# View app logs
sudo journalctl -u gbgolf -n 100

# View fetch logs
cat /opt/GBGolfOptimizer/logs/fetch.log

# Check cron schedule
crontab -l

# Manual fetch (as deploy user)
cd /opt/GBGolfOptimizer && FLASK_APP=gbgolf.web:create_app .venv/bin/flask fetch-projections
```
