# Document 5: Frontend and UI/UX Audit

**Project Name:** EduMind  
**Audit Date:** November 2026  
**Auditor Role:** Senior Frontend Engineer & UI/UX Specialist  

---

## 1. Frontend Architecture & Design Overview

The user interface of EduMind is composed of **56 Django HTML templates** styled with vanilla CSS and styled-component blocks embedded directly inside `<style>` tags within individual templates, complemented by a modest global stylesheet in `static/css/`.

Interactive logic is implemented with native JavaScript. The frontend does not utilize npm, Webpack, Vite, Tailwind CLI, or a modern JavaScript framework.

---

## 2. Categorized UI/UX and Functional Issues

### Critical Severity Issues

| ID | Location / Template | Issue Description | Impact |
|---|---|---|---|
| **UI-CRIT-01** | `templates/test.html` (L1-L30) | **Answer Key & Explanations Exposed in Client DOM:** View dumps all answers directly into inline JS variable `const questions = JSON.parse('{{ questions_json\|escapejs }}');`. Anyone opening Browser DevTools -> Console can inspect the correct answer and explanation for every question during an ongoing exam. | Complete loss of exam integrity; trivial cheating. |
| **UI-CRIT-02** | `templates/test.html` | **Total Data Loss on Page Refresh / Disconnect:** Answers and timers are stored solely in volatile browser memory (`let answers = [];`). If a student accidentally presses F5, swipes back on mobile, or encounters network fluctuation, all progress is wiped with no session resume capability. | Severe candidate disruption and loss of exam attempts. |

---

### High Severity Issues

| ID | Location / Template | Issue Description | Impact |
|---|---|---|---|
| **UI-HIGH-01** | `templates/bank_ibps_po.html`, `bank_rrb_po.html`, `bank_sbi_po.html`, `bank_rrb_assistnat.html`, `bank_sbi_assistant.html` | **Mock Test Action Buttons are Dead Anchor Links (`href="#"`):** Over 60 individual mock test cards in the banking section render styled "Start Test" and "Take Mock Test" buttons that point to `href="#"`. | High user frustration; users click buttons and nothing happens. |
| **UI-HIGH-02** | `templates/ssc_chsl.html`, `ssc_cpo.html`, `ssc_gd_constable.html`, `ssc_je.html`, `ssc_mts.html`, `ssc_stenographer.html` | **SSC Section Dead End Links:** Identical dead-link pattern across SSC exam views. Cards render with realistic badges (e.g. "Tier 1 - Mock Test 1 to 10") but all buttons link to `#`. | Features appear implemented on visual demo but are functionally non-existent. |
| **UI-HIGH-03** | `templates/railway_ntpc.html`, `railway_group_d.html`, `railway_assistant_loco_piolet.html` | **Railway Exam Dead End Links:** Each page renders 10 mock test cards where buttons point to `#`. Only RRB JE CBT-1 (`rrb_je_cbt1_mock_tests.html`) and RRB ALP (`railway_assistant_loco_piolet.html` select tests) link to valid routes. | Disconnected user experience. |
| **UI-HIGH-04** | `templates/settings.html` | **Completely Blank Template:** File contains only 20 bytes: `{% extends "base.html" %}`. Navigating to `/settings/` displays an empty white page with only the navbar. | Broken navigation target from user profile menu. |
| **UI-HIGH-05** | `templates/profile.html` | **Profile Edit Form is a Dead Form:** Renders form fields for First Name, Last Name, Email, and Mobile Number, but the form has no `method="POST"`, no action URL, and no submit handler in `accounts/views.py`. | Users cannot update their profile information. |

---

### Medium Severity Issues

| ID | Location / Template | Issue Description | Impact |
|---|---|---|---|
| **UI-MED-01** | `templates/result_detail.html` vs `templates/test_result_detail.html` | **Duplicate Inconsistent Result Detail Screens:** The app has two separate result detail views with completely different designs, colors, and layout hierarchies. Submitting a test sends user to `result_detail.html`, while clicking a test from the Performance dashboard sends user to `test_result_detail.html`. | Disorienting and inconsistent branding. |
| **UI-MED-02** | `templates/home.html` (L120, L310) | **Hardcoded URL Links:** Links use hardcoded string literals `href="/register/"` and `href="/login/"` instead of Django's `{% url 'register' %}` and `{% url 'login' %}`. If URL prefixes or subpath routing changes, links break. | Fragile URL routing. |
| **UI-MED-03** | `templates/verify registrations.html` | **Template Filename Contains Space:** File is named `verify registrations.html` with a physical whitespace character in the file name, referenced via `render(request, "verify registrations.html", ...)`. | Risky on Linux/Unix production filesystems; violates Python/Django naming conventions. |
| **UI-MED-04** | `templates/test_v2.html` | **Orphaned / Abandoned Sectional Timer Template:** Contains advanced sectional timer UI and question palette logic, but is not attached to any URL route in `accounts/urls.py`. | Dead codebase asset. |

---

### Low Severity Issues

| ID | Location / Template | Issue Description | Impact |
|---|---|---|---|
| **UI-LOW-01** | Throughout templates | **Massive CSS Duplication:** Every single template repeats 200–500 lines of identical CSS inside `<style>` tags (e.g. glassmorphism navbar, gradient buttons, card styles) rather than importing shared classes from `static/css/style.css`. | Code bloat, increased page weight, high maintenance overhead. |
| **UI-LOW-02** | Multiple templates | **Spelling Errors in File Names & Templates:** Files named `bank_rrb_assistnat.html` (misspelling of "assistant"), `railway_assistant_loco_piolet.html` (misspelling of "pilot"), and `Performanace_analysis.docx`. | Unprofessional codebase hygiene. |
| **UI-LOW-03** | `templates/base.html` | **Accessibility (a11y) Gaps:** Lack of ARIA labels on modal dialogs, exam question radio buttons lack associated `<label for="...">` IDs, color contrast on some light-green buttons fails WCAG AA standards. | Poor accessibility for screen readers and keyboard navigation. |

