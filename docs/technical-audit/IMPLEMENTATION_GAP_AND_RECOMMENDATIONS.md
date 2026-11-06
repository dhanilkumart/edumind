# Document 10: Implementation Gap Analysis & Pre-Deployment Roadmap

**Project Name:** EduMind  
**Audit Date:** November 2026  
**Auditor Role:** Senior Software Architect & Lead DevOps Engineer  

---

## 1. Categorized Implementation Gap & Work Items

Before EduMind can be safely deployed and operated in a live production VPS environment with real students taking competitive examinations, the following work items must be executed.

### Category 1: MUST FIX BEFORE PRODUCTION DEPLOYMENT (P0 - Critical Blockers)

| Task ID | Component / Source File | Description of Required Fix | Risk if Omitted |
|---|---|---|---|
| **GAP-P0-01** | `accounts/views.py` (L170-L182) | **Sanitize Question Serializer:** Remove `correct_option` and `explanation` from the question payload sent to `test.html`. Keep answers exclusively in backend database. | Candidates can cheat trivially by inspecting browser JavaScript memory. |
| **GAP-P0-02** | `edumind/settings.py` (L23-L28) | **Production Security Hardening:** Move `SECRET_KEY`, `DEBUG = False`, and `ALLOWED_HOSTS` to environment variables (`.env`). | Full server file paths and database credentials exposed on 500 errors; session forgery. |
| **GAP-P0-03** | `edumind/settings.py`, `requirements.txt` | **PostgreSQL Configuration:** Add `psycopg2-binary>=2.9.9` and configure `DATABASES` dictionary to connect to PostgreSQL on production VPS. Dump clean data from `db.sqlite3` and seed PostgreSQL. | SQLite database locks and performance collapse under concurrent student exams. |
| **GAP-P0-04** | `accounts/views.py` (L3645-L3690), `settings.py` | **External Service Configuration (SMS & Email):** Add MSG91 credentials and SMTP settings to `.env`. Fix unhandled `RuntimeError` on missing keys so registration does not throw 500. Add `requests` to `requirements.txt`. | Public registration and password resets completely crash on production. |
| **GAP-P0-05** | `accounts/views.py` (L1723-L2005) | **Database Transaction Atomicity:** Wrap `submit_test` inside `@transaction.atomic`. Ensure `TestResult`, `UserAnswer`, and `TestAttempt` commit together or roll back on error. | Incomplete, corrupted result records during concurrent exam submissions. |
| **GAP-P0-06** | `accounts/views.py` (L1215, L2498, L2650, L3340) | **Eliminate Overwritten View Functions:** Remove duplicate function definitions (`cat_full_mock_tests`, `cat_session_tests`, `olympiad_class`, `get_olympiad_mock_test`) to eliminate confusing dead code. | Unpredictable routing behavior during runtime execution. |
| **GAP-P0-07** | `edumind/settings.py` | **Configure Media Files:** Add `MEDIA_ROOT` and `MEDIA_URL` settings for uploaded question files. | Uploaded Excel spreadsheets cannot be safely stored or audited. |

---

### Category 2: RECOMMENDED BEFORE PRODUCTION DEPLOYMENT (P1 - High Priority)

| Task ID | Component / Source File | Description of Required Fix | Benefit |
|---|---|---|---|
| **GAP-P1-01** | `templates/test.html` | **Periodic Local Auto-Save (Exam Persistence):** Save question selections to `localStorage` or send a debounced ping to a session store so refreshing the browser does not wipe exam answers. | Protects students from lost test progress due to accidental reloads or network drops. |
| **GAP-P1-02** | `templates/*.html` (Banking, SSC, Railway) | **Fix Dead Anchor Links (`href="#"`):** Replace visual `#` buttons with dynamic links to existing database mock tests or display an "Upcoming / Available Soon" badge. | Prevents severe user frustration and perceived application unresponsiveness. |
| **GAP-P1-03** | `templates/settings.html`, `profile.html` | **Implement Settings & Profile Update:** Build POST handling in `accounts/views.py` for user profile updates and populate the empty `settings.html` template. | Delivers basic expected user account management. |
| **GAP-P1-04** | `accounts/models.py` | **Dynamic Scoring Configuration:** Add `marks_per_correct` (default 3.0) and `negative_marks` (default 1.0) fields to `MockTest` model rather than hardcoding exam-specific logic in `submit_test`. | Allows staff to create exams with custom marking rules without modifying Python code. |
| **GAP-P1-05** | Repository Hygiene | **Remove Checked-In Artifacts:** Add `venv/`, `backup_data.json`, `edumind.zip`, and `*.docx` to `.gitignore`. Ensure `requirements.txt` is encoded in clean UTF-8. | Keeps repository lightweight and prevents deployment confusion. |
| **GAP-P1-06** | `templates/test_result_detail.html` vs `result_detail.html` | **Consolidate Result Screens:** Retire redundant templates and unify around a single, responsive test review interface. | Consistent user experience and halved maintenance overhead. |

---

### Category 3: CAN BE ADDRESSED AFTER LAUNCH (P2 - Post-Launch Enhancements)

| Task ID | Component / Source File | Description | Benefit |
|---|---|---|---|
| **GAP-P2-01** | `accounts/views.py` | **Modularize Views Package:** Split the 4,158-line `views.py` into smaller focused modules: `accounts/views/auth.py`, `exams.py`, `dashboard.py`, `analytics.py`, `admin.py`. | Greatly improves developer productivity and reduces merge conflicts. |
| **GAP-P2-02** | `accounts/models.py`, `test_v2.html` | **Activate Sectional Timed Exams:** Implement models and logic for multi-section tests (e.g. CAT 40-min Verbal, 40-min DILR, 40-min Quant) where sections unlock sequentially. | Mirrors real-world CAT/Banking exam conditions. |
| **GAP-P2-03** | Global CSS / Frontend | **Refactor Shared CSS:** Extract repeated styles across 56 templates into centralized CSS files in `static/css/` to optimize browser caching. | Reduces page payload by up to 60% and accelerates load times. |
| **GAP-P2-04** | Security / Middleware | **Rate Limiting & Anti-Brute-Force:** Integrate `django-ratelimit` or Redis-backed rate limiters on public login and OTP endpoints. | Prevents SMS abuse and brute-force attacks. |

---

## 2. Immediate Recommended Next Steps

1. **Review and Approve Audit Findings:** Review the technical audit deliverables inside `docs/technical-audit/`.
2. **Execute Critical Security Fix (P0-01):** Remove the answer key from `test_view` so question answers are never exposed to the client.
3. **Provision PostgreSQL & Run Data Migration:** Dump clean data from `db.sqlite3` using Django fixtures and test ingestion into a local/staging PostgreSQL instance.
4. **Environment Externalization:** Configure `.env` and adjust `settings.py` for production mode.
5. **VPS Deployment Execution:** Set up Ubuntu VPS, configure Nginx, Gunicorn, systemd services, SSL certificates, and automated backup crons.

