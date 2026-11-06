# Document 7: Windows Local Setup & Execution Guide

**Project Name:** EduMind  
**Audit Date:** November 2026  
**Auditor Role:** DevOps Engineer & Django Backend Specialist  

---

## 1. Prerequisites & Environment Verification

Before running EduMind on Windows, ensure the following tools are installed:

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Python Version:** Python 3.12 or 3.13 (Python 3.13.5 recommended; Python 3.14+ may encounter third-party wheel issues with some C-extensions)
- **Git for Windows**
- **PowerShell 5.1+** or **PowerShell 7**

---

## 2. Step-by-Step Windows Local Setup

### Step 1: Open PowerShell in Project Root
Open PowerShell and navigate to the project directory:
```powershell
cd "d:\Dhanil\Git Repositeries\edumind"
```

### Step 2: Create a Clean Python Virtual Environment
> [!NOTE]
> The existing `venv` folder in the repository contains hardcoded paths to a previous developer machine (`C:\Python313\python.exe` and `C:\Users\ROHITH\Documents\EduMind\...`). Do **not** use the checked-in `venv`. Create a fresh local virtual environment:

```powershell
# Create new virtual environment named .venv
python -m venv .venv

# Activate the virtual environment in PowerShell
.\.venv\Scripts\Activate.ps1
```
*(If you encounter execution policy restrictions, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 3: Install Required Dependencies
> [!WARNING]
> The repository `requirements.txt` was encoded in UTF-16 LE and is missing the `requests` library needed for SMS dispatch. Run the following command:

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install Django==6.0.7 openpyxl==3.1.5 asgiref==3.11.1 gunicorn==26.0.0 sqlparse==0.5.5 tzdata==2026.3 requests
```

### Step 4: Verify Database State
The project already includes a populated SQLite database `db.sqlite3` with 3,216 questions, 64 mock tests, and 9 subjects.

Run Django migration checks to confirm database schema alignment:
```powershell
python manage.py showmigrations
```
All migrations `0001_initial` through `0022_question_section` should show `[X]`.

If any migration is unapplied, run:
```powershell
python manage.py migrate
```

### Step 5: Create a Superuser Account (Optional)
To log into `/admin/` and `/upload_questions/`:
```powershell
python manage.py createsuperuser
```
*(Enter username, email, and password as prompted).*

### Step 6: Start the Development Server
```powershell
python manage.py runserver 127.0.0.1:8000
```

### Step 7: Access the Application
Open a web browser and visit:
- **Landing Page:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Student Login:** [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
- **Admin Dashboard:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Question Upload:** [http://127.0.0.1:8000/upload_questions/](http://127.0.0.1:8000/upload_questions/)

---

## 3. Known Local Blockers & Workarounds

1. **SMS Provider Missing Credentials Error:**
   When attempting to register via `/register/`, the code calls `send_sms_otp` which checks `MSG91_AUTHKEY`. Since it is not defined in `settings.py`, an error occurs.
   - *Temporary Workaround for Local Testing:* Create user accounts directly via `python manage.py createsuperuser` or through the Django admin portal (`/admin/auth/user/add/`), then log in via `/login/`.
2. **Missing `requests` Package:**
   If you install only from `requirements.txt` without `requests`, OTP-related views will crash with `ModuleNotFoundError`.

