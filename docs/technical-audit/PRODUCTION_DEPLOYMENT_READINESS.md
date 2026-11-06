# Document 8: Production Deployment Readiness Assessment

**Project Name:** EduMind  
**Audit Date:** November 2026  
**Auditor Role:** DevOps Engineer & Senior Infrastructure Architect  
**Target Environments:** Hostinger Cloud VPS (Ubuntu 24.04 LTS) or DigitalOcean Droplet (Ubuntu 24.04 LTS)  

---

## 1. Production Readiness Scorecard

| Assessment Category | Current Status | Readiness Score | Critical Blocker |
|---|---|---|---|
| **Security & Secrets** | Insecure | ❌ 1 / 10 | Hardcoded `SECRET_KEY`, `DEBUG = True`, `ALLOWED_HOSTS = ["*"]` |
| **Database Architecture** | Incompatible | ❌ 2 / 10 | SQLite in use; missing PostgreSQL driver & connection logic |
| **Static & Media Asset Handling**| Incomplete | ⚠️ 4 / 10 | `STATIC_ROOT` defined, but no `MEDIA_ROOT` for uploaded files |
| **Web / WSGI Server Config** | Incomplete | ⚠️ 5 / 10 | Gunicorn listed in requirements, but no systemd service or gunicorn config file |
| **External Service Integration** | Broken | ❌ 2 / 10 | MSG91 and SMTP unconfigured; registration throws 500 |
| **Code Hygiene & Packaging** | Poor | ⚠️ 3 / 10 | UTF-16 requirements file, checked-in `.venv`, `.zip` file, docx files in git |

**Overall Deployment Readiness Verdict:** **NOT READY FOR PRODUCTION DEPLOYMENT**  
*Direct deployment of the existing codebase to production will result in security exposure, data loss on restart, and broken registration flows.*

---

## 2. Target Production Architecture

```mermaid
graph TD
    Client([Internet / Candidates])
    
    subgraph Cloud VPS (Hostinger / DigitalOcean Ubuntu 24.04)
        Firewall["UFW Firewall (Ports 80, 443, SSH)"]
        Certbot["Let's Encrypt SSL / Certbot"]
        Nginx["Nginx Reverse Proxy & Web Server"]
        
        subgraph Application Services
            Systemd["Systemd Service (edumind.service)"]
            Gunicorn["Gunicorn WSGI Master (3 Workers)"]
            Django["Django App (edumind.wsgi:application)"]
        end
        
        subgraph Storage & Data
            StaticFiles["/var/www/edumind/staticfiles/"]
            MediaFiles["/var/www/edumind/media/"]
            PostgreSQL[(PostgreSQL 16 Service<br/>edumind_db)]
            Backups["Automated Nightly Cron Backups<br/>(pg_dump + gzip)"]
        end
    end

    Client -->|HTTPS:443| Firewall
    Firewall --> Nginx
    Nginx -->|Static Requests| StaticFiles
    Nginx -->|Media Requests| MediaFiles
    Nginx -->|Proxy Pass unix:/run/edumind.sock| Gunicorn
    Systemd -->|Manages| Gunicorn
    Gunicorn --> Django
    Django -->|TCP / UNIX Socket| PostgreSQL
    PostgreSQL -.-> Backups
```

---

## 3. Required Infrastructure & Configuration Changes

### 1. Externalize Environment Variables (`.env`)
Create a production `.env` file outside version control:
```ini
DJANGO_ENV=production
DEBUG=False
SECRET_KEY=generate_strong_64_character_random_secret_here
ALLOWED_HOSTS=edumind.yourdomain.com,www.edumind.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://edumind.yourdomain.com,https://www.edumind.yourdomain.com

DB_NAME=edumind_db
DB_USER=edumind_user
DB_PASSWORD=strong_postgres_password
DB_HOST=127.0.0.1
DB_PORT=5432

MSG91_AUTHKEY=your_msg91_authkey
MSG91_FLOW_TEMPLATE_ID=your_template_id
MSG91_FLOW_API_URL=https://control.msg91.com/api/v5/flow/
MSG91_OTP_VARIABLE_NAME=OTP

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_smtp_key
DEFAULT_FROM_EMAIL=no-reply@yourdomain.com
```

### 2. Configure `settings.py` for Database & Storage
Refactor `DATABASES` in `edumind/settings.py` to conditionally load PostgreSQL when `DJANGO_ENV=production`:
```python
import os
import dj_database_url  # or custom dictionary from os.getenv

if os.getenv("DJANGO_ENV") == "production":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
```

### 3. Add Media Files Configuration
Add to `settings.py`:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 4. Gunicorn Systemd Service Unit (`/etc/systemd/system/edumind.service`)
```ini
[Unit]
Description=Gunicorn daemon for EduMind Application
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/edumind
EnvironmentFile=/var/www/edumind/.env
ExecStart=/var/www/edumind/.venv/bin/gunicorn \
          --access-logfile /var/log/edumind/gunicorn_access.log \
          --error-logfile /var/log/edumind/gunicorn_error.log \
          --workers 3 \
          --bind unix:/run/edumind.sock \
          edumind.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. Nginx Reverse Proxy Configuration (`/etc/nginx/sites-available/edumind`)
```nginx
server {
    server_name edumind.yourdomain.com;

    client_max_body_size 20M;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/edumind/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /var/www/edumind/media/;
        expires 30d;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/edumind.sock;
    }

    listen 80;
}
```

---

## 4. Production Backup Strategy

### Automated PostgreSQL Backup Cron (`/etc/cron.daily/backup-edumind-db`)
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/edumind"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
pg_dump -U edumind_user -h 127.0.0.1 edumind_db | gzip > "$BACKUP_DIR/edumind_db_$TIMESTAMP.sql.gz"

# Retain 14 days of backups
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +14 -delete
```

