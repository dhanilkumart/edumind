# Document 2: Module and Feature Inventory

**Project Name:** EduMind  
**Audit Date:** November 2026  
**Auditor Role:** Senior Software Architect & Django Backend Engineer  

---

## 1. Inventory Summary & Classification Matrix

Features are classified into six distinct operational states:
1. **Fully Implemented:** Front-to-back integration complete, operational with real database models.
2. **Partially Implemented:** Functional in some paths but lacking robust error handling, data bindings, or validation.
3. **UI-Only / Mock-Data:** Templates exist and render, but buttons are dead, forms lack endpoints, or data is hardcoded HTML.
4. **Incomplete Backend Integration:** View logic or model exists but is not wired to templates or URLs properly.
5. **Not Implemented:** Placeholders, zero-byte templates, or missing handler routes.
6. **Functional Problems / Faulty:** Implemented but contains severe bugs, security flaws, or mathematical errors.

---

## 2. Comprehensive Module Inventory

| Module / Feature | Related Screens | Backend Implementation | Database Models | Implementation Status | Functional Evaluation & Deficiencies |
|---|---|---|---|---|---|
| **User Registration & 2FA OTP** | `register.html`, `verify registrations.html` | `register`, `verify_registration`, `resend_registration_otp` | `PendingRegistration`, `Profile`, `User` | **Partially Implemented / Broken SMS** | Dual OTP (Email + Mobile). Uses temporary `PendingRegistration` model. If MSG91 credentials aren't set, registration raises unhandled runtime exceptions. |
| **User Authentication (Login/Logout)** | `login.html`, `base.html` | `login_view`, `logout_view` | `User`, `Profile` | **Fully Implemented** | Supports authentication by username or email. Standard session creation and redirect to dashboard. |
| **Password Reset via OTP** | `forgot_password.html`, `verify_password_otp.html`, `set_new_password.html` | `forgot_password`, `verify_password_reset_otp`, `set_new_password` | `PasswordResetOTP`, `User` | **Partially Implemented / Fragile** | Allows resetting via email or mobile OTP. Relies on SMS/Email which fails if environment variables are missing. |
| **Student Dashboard** | `dashboard.html` | `dashboard` | `MockTest`, `TestResult`, `Subject` | **Fully Implemented** | Displays quick metrics, recent test results, and exam category links. |
| **Exam Catalog Navigation** | `exams.html`, `subjects.html` | `exams`, `subjects` | `Subject`, `MockTest` | **Fully Implemented** | Categorizes tests into CAT, Bank, SSC, Railway, Olympiad, etc. |
| **Mock Test Runner (Exam Engine)** | `test.html` | `test_view` (L152) | `MockTest`, `Question` | **Faulty / Critical Vulnerability** | Runs countdown timer, question palette, answer selection. **Critical Flaw:** Full answer key and explanations are serialized into client-side JS (`questions_json`). |
| **Test Submission & Scoring Engine** | None (AJAX endpoint) | `submit_test` (L1723) | `TestResult`, `UserAnswer`, `TestAttempt` | **Fully Implemented / Hardcoded Scoring** | Receives JSON payload, calculates score, saves question responses. Hardcoded scoring rules (RRB ALP: +1/-0.333, others: +3/-1). No transaction wrapping. |
| **Test Result View & Review** | `test_result_detail.html`, `result_detail.html`, `review_test.html`, `review.html` | `test_result_detail`, `result_detail`, `review_test`, `review` | `TestResult`, `UserAnswer`, `Question` | **Partially Implemented / Duplicate Routes** | Two parallel result detail views (`result/<id>/` vs `performance/test-result/<id>/`). Redundant templates. |
| **Candidate Test Ranking (Leaderboard)** | `test_ranking.html` | `test_ranking` (L3101) | `MockTest`, `TestResult`, `User` | **Fully Implemented** | Displays leaderboards with rank, candidate username, score, accuracy, and date. Filters best attempts. |
| **Performance Analysis Dashboard** | `performance_analysis.html`, `category_performance.html` | `performance`, `category_performance` | `TestResult`, `MockTest`, `Subject` | **Fully Implemented** | Shows overall accuracy, test count, subject breakdowns, and graphical progress cards. |
| **Previous Tests History** | `previous_tests.html` | `previous_tests` (L504) | `TestResult` | **Fully Implemented** | Lists all previous attempts for logged-in user with links to results. |
| **Question Ingestion (Excel Upload)** | `upload_questions.html` | `upload_questions` (L2125) | `Question`, `MockTest` | **Fully Implemented (Staff Only)** | Ingests `.xlsx` files using `openpyxl`. Parses columns for Question, Option A-D, Correct Answer, Explanation. |
| **Banking Exam Module** | `banking.html`, `bank_exam_tests.html`, `bank_*` templates | `banking`, `bank_exam_tests`, `ibps_po`, `sbi_po`, etc. | `Subject`, `MockTest` | **Partially Implemented / UI-Only dead links** | 6 bank templates have extensive hardcoded `#` anchor links. Only tests existing in database render dynamic links. |
| **SSC Exam Module** | `ssc_cgl.html`, `ssc_chsl.html`, `ssc_je.html`, `ssc_mts.html`, etc. | `ssc_cgl`, `ssc_chsl`, `ssc_je`, `ssc_mts`, `ssc_gd`, etc. | `Subject`, `MockTest` | **Partially Implemented / UI-Only dead links** | Several SSC views render static cards with `#` links. Many tests are unlinked to real `MockTest` IDs. |
| **Railway Exam Module** | `railway.html`, `railway_assistant_loco_piolet.html`, `railway_group_d.html`, `railway_ntpc.html`, `rrb_je_cbt1_mock_tests.html` | `railway`, `rrb_je_cbt1_mock_tests`, `rrb_alp`, `rrb_ntpc`, `rrb_group_d` | `Subject`, `MockTest` | **Partially Implemented** | RRB JE CBT-1 and ALP have real mock test links; NTPC and Group D contain static mock test tables with `#` links. |
| **CAT Module** | `cat.html`, `cat_full_mock_tests.html`, `cat_session_tests.html` | `cat`, `cat_full_mock_tests`, `cat_session_tests` | `Subject`, `MockTest` | **Partially Implemented / Duplicate Views** | Functions `cat_full_mock_tests` and `cat_session_tests` are defined twice in `views.py`. |
| **School Olympiad Module** | `olympiad.html`, `olympiad_class.html`, `olympiad_subject.html`, `olympiad_test.html` | `olympiad`, `olympiad_class`, `olympiad_subject`, `olympiad_test` | `Subject`, `MockTest`, `Question` | **Partially Implemented / Fallback Logic** | Contains hardcoded programmatic generators (`get_olympiad_mock_test` defined twice). Creates tests on the fly if missing. |
| **User Profile Management** | `profile.html` | `profile` (L526) | `User`, `Profile` | **UI-Only / Incomplete** | Displays user profile info (name, email, phone). Profile edit form has no POST handler or update logic. |
| **Account Settings** | `settings.html` | `settings_view` (L1033) | None | **Not Implemented (Empty)** | Template `settings.html` contains 20 bytes: `{% extends "base.html" %}`. Completely blank. |
| **Sectional Timed Tests** | `test_v2.html` | None (Unlinked) | `TestSection`, `MockTest` | **Incomplete Backend Integration** | Model `TestSection` exists; migration 0021 added `timing_mode`. However, `test_v2.html` is unlinked in `urls.py`. |
| **Specialized Exam Pages** | None (inline renders) | `tenth_pass`, `twelfth_pass`, `graduate`, `engineering`, `specialized` | `Subject`, `MockTest` | **UI-Only / Stub** | Simple redirects or static subject renders without distinct specialized catalogs. |

