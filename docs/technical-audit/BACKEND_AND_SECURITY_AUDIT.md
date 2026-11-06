# Document 6: Backend and Security Audit

**Project Name:** EduMind  
**Audit Date:** November 2026  
**Auditor Role:** Senior Software Architect, Django Backend Engineer & Security Auditor  

---

## 1. Backend Architecture & Code Structure

The backend consists of a single application `accounts` within the `edumind` Django project. The entire application business logic is concentrated within a single file: `accounts/views.py` (4,158 lines).

### Code Quality Findings

1. **Extreme Monolith (`views.py`):**
   - 4,158 lines containing 79 separate function definitions.
   - Mixes authentication, OTP dispatch, test administration, scoring, reporting, Excel file parsing, and admin statistics in one file.
   - Repeated inline imports (e.g. `import json`, `import re`, `from django.shortcuts import render` repeated in the middle of functions).
2. **Duplicate Function Definitions (Dead Code / Overwritten Views):**
   In Python, defining a function with the same name twice in a module causes the second definition to silently overwrite the first:
   - `cat_full_mock_tests`: Defined at L1215 and again at L2498.
   - `cat_session_tests`: Defined at L1254 and again at L2536.
   - `olympiad_class`: Defined at L2650 and again at L3340.
   - `get_olympiad_mock_test`: Defined at L3373 and again at L3483.
   The earlier implementations are permanently unreachable dead code.
3. **Hardcoded Examination Business Logic:**
   In `submit_test` (L2011-L2025):
   ```python
   if "ALP" in mock_test.name.upper():
       score = correct - (wrong / 3)
   else:
       score = (correct * 3) - (wrong * 1)
   ```
   Negative marking and scoring weightings are hardcoded into Python string comparisons rather than stored as configurable attributes on the `MockTest` or `Subject` model (e.g. `marks_per_question`, `negative_marks`).
4. **Non-Atomic Exam Submission:**
   In `submit_test` (L1723), the view creates `TestResult`, iterates over questions to create dozens/hundreds of `UserAnswer` records, and creates a `TestAttempt`. This operation is **not wrapped in `@transaction.atomic`**. If an unhandled exception or database lock occurs during iteration, orphaned `TestResult` records remain in the database without corresponding answers.

---

## 2. Security Vulnerability Assessment

### Critical Vulnerabilities

#### SEC-CRIT-01: Correct Answer & Explanation Leakage in Exam API/View
- **Location:** `accounts/views.py` (L170-L182) and `templates/test.html` (L3)
- **Vulnerability:** When a candidate loads `/test/<test_id>/`, the view builds a question dictionary containing:
  ```python
  questions_data.append({
      "id": question.id,
      "question_no": question.question_no,
      "question": question.question,
      "options": [question.option_a, question.option_b, question.option_c, question.option_d],
      "correct_option": question.correct_option,  # <--- LEAKED TO CLIENT
      "explanation": question.explanation or "",    # <--- LEAKED TO CLIENT
  })
  ```
  This is serialized directly into the HTML document as JavaScript:
  `const questions = JSON.parse('{{ questions_json|escapejs }}');`
- **Impact:** Any candidate can open Chrome/Firefox DevTools (F12), inspect the `questions` array, and score 100% on any exam. Exam integrity is completely compromised.
- **Remediation:** Remove `correct_option` and `explanation` from `test_view`. Retain answer keys exclusively on the server side in PostgreSQL/SQLite.

#### SEC-CRIT-02: Hardcoded Production SECRET_KEY and DEBUG Mode Active
- **Location:** `edumind/settings.py` (L23-L28)
- **Vulnerability:**
  ```python
  SECRET_KEY = 'django-insecure-h%-7l*jh6x8nd11b4q_5j5^+r#u3qz5g&4^d1l$jw5-@8eu7xo'
  DEBUG = True
  ALLOWED_HOSTS = ["*"]
  ```
- **Impact:**
  - With `DEBUG = True`, any 500 error prints full stack traces, database schema, local file paths, and environment settings to the browser.
  - Hardcoded `SECRET_KEY` permits session forgery and cookie tampering if source code is exposed.
  - `ALLOWED_HOSTS = ["*"]` exposes the app to HTTP Host header poisoning and cache poisoning.
- **Remediation:** Load `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` from an environment file (`.env`) via `os.environ` or `django-environ`.

---

### High Vulnerabilities

#### SEC-HIGH-01: Unhandled SMS/Email Gateway Crashes in Public Auth Endpoints
- **Location:** `accounts/views.py` (L3645-L3690)
- **Vulnerability:**
  `send_sms_otp` checks `getattr(settings, "MSG91_AUTHKEY", "")`. Because `MSG91_AUTHKEY` is absent from `settings.py`, calling registration or password reset raises a `RuntimeError("SMS provider is not configured.")`. This results in unhandled 500 server errors for end users trying to register.
- **Remediation:** Implement fallback logging or graceful error responses when messaging providers are unconfigured.

#### SEC-HIGH-02: Excel File Ingestion Denial of Service & Validation Gaps
- **Location:** `accounts/views.py` (L2125-L2250)
- **Vulnerability:** In `upload_questions`, an uploaded `.xlsx` file is loaded directly into server memory with `openpyxl.load_workbook(excel_file, data_only=True)`. There is no limit on upload file size, no validation on the number of rows, and no MIME type verification beyond file extension. A malicious staff account could upload a 50 MB decompression bomb ("billion laughs" or zip bomb) that exhausts server memory.
- **Remediation:** Enforce maximum file size limits (e.g. 5 MB) and validate worksheet row count limits.

---

### Medium Vulnerabilities

#### SEC-MED-01: Inconsistent Route Authentication Protection
- **Location:** `accounts/views.py` and `accounts/urls.py`
- **Vulnerability:** While most exam routes use `@login_required`, some routes rely on manual `if not request.user.is_authenticated: return redirect("login")` (e.g., L506 `previous_tests`, L528 `profile`), while others lack decorators entirely (`banking`, `ssc`, `railway`). While public category browsing may be intentional, the implementation lacks an overarching permission architectural standard.
- **Remediation:** Standardize authentication enforcement across views or via Django middleware.

#### SEC-MED-02: Missing Rate Limiting on Authentication Endpoints
- **Location:** `/login/`, `/register/`, `/verify-registration/`, `/forgot-password/`
- **Vulnerability:** No rate limiting (e.g. via `django-ratelimit` or Nginx `limit_req`) is configured on OTP verification or password reset forms. Attackers can brute-force 6-digit OTP codes (1,000,000 possibilities) or spam SMS gateways, draining credits.
- **Remediation:** Enforce Nginx rate-limiting zones (`rate=5r/m`) on all authentication endpoints and lock accounts after 5 failed OTP attempts.

