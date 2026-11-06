# Document 9: Testing and Validation Plan

**Project Name:** EduMind  
**Audit Date:** November 2026  
**Auditor Role:** Senior QA Architect & Lead Test Automation Engineer  

---

## 1. Existing Automated Test Audit

- **Test Suite Location:** `accounts/tests.py`
- **File Size:** 60 bytes
- **Contents:**
  ```python
  from django.test import TestCase

  # Create your tests here.
  ```
- **Finding:** **ZERO automated tests exist in the entire codebase.** There are no unit tests, no model tests, no view tests, and no integration tests. Coverage is 0%.

---

## 2. Manual Testing Checklist (Comprehensive Workflow Verification)

### Phase 1: Authentication & Onboarding
- [ ] **TC-AUTH-01:** Registration form validation (empty fields, mismatched passwords, duplicate username/email/mobile).
- [ ] **TC-AUTH-02:** Email OTP generation, expiry check (countdown timer), and delivery via SMTP.
- [ ] **TC-AUTH-03:** Mobile OTP generation, expiry check, and SMS dispatch via MSG91 Flow API.
- [ ] **TC-AUTH-04:** Dual verification completion: ensure `User` account is created only after both OTPs match.
- [ ] **TC-AUTH-05:** Login via valid username and valid password.
- [ ] **TC-AUTH-06:** Login via valid email and valid password.
- [ ] **TC-AUTH-07:** Login rejection on incorrect password with error messaging.
- [ ] **TC-AUTH-08:** Password reset request via registered email or mobile.
- [ ] **TC-AUTH-09:** Set new password and verify previous password is superseded.
- [ ] **TC-AUTH-10:** Logout functionality and session destruction.

### Phase 2: Examination Lifecycle & Integrity
- [ ] **TC-EXAM-01:** Test launch: Verify `/test/<id>/` renders correct question count and timer matches `mock_test.duration_minutes`.
- [ ] **TC-EXAM-02:** Security Check: Inspect browser DevTools network and console tabs. Verify answers and explanations are NOT visible in raw HTML/JS payload.
- [ ] **TC-EXAM-03:** Option selection: Select Option A; verify question palette marks question as green (Answered).
- [ ] **TC-EXAM-04:** Option deselection / clearing response: Select "Clear Response"; verify state reverts to red/unanswered.
- [ ] **TC-EXAM-05:** Mark for Review: Verify button toggles state to purple.
- [ ] **TC-EXAM-06:** Question time tracking: Dwell on question 1 for 30 seconds; switch to question 2; verify payload accurately records 30 seconds for question 1.
- [ ] **TC-EXAM-07:** Countdown Timer: Allow timer to count down to 00:00:00. Verify automatic auto-submission fires smoothly without UI lockup.
- [ ] **TC-EXAM-08:** Manual Submission Modal: Click "Submit Test"; verify warning shows answered count, unanswered count, and marked count before confirming.
- [ ] **TC-EXAM-09:** Double Submission Protection: Rapidly double-click submit button; verify server records only ONE `TestResult`.
- [ ] **TC-EXAM-10:** Scoring Accuracy (Standard Test): Answer 10 correct, 2 wrong. Verify `Score = (10 * 3) - (2 * 1) = 28` and `Accuracy = (10 / 12) * 100 = 83.33%`.
- [ ] **TC-EXAM-11:** Scoring Accuracy (RRB ALP Test): Answer 12 correct, 3 wrong. Verify `Score = 12 - (3 / 3) = 11`.
- [ ] **TC-EXAM-12:** Zero-answer submission: Submit test without answering any questions; verify score is 0 and no division-by-zero crashes occur.

### Phase 3: Reporting & Leaderboards
- [ ] **TC-REP-01:** Test Result Detail: View post-test review screen. Verify all questions display user choice, correct choice, and explanation.
- [ ] **TC-REP-02:** Performance Dashboard: Check `/performance/` to ensure total tests taken, overall score, and accuracy metrics refresh immediately.
- [ ] **TC-REP-03:** Leaderboard Ranking: Check `/performance/ranking/<test_id>/`. Verify candidates are ranked highest to lowest score, ties broken by timestamp.
- [ ] **TC-REP-04:** Historical Tests: Check `/previous_tests/` to confirm completed test appears with timestamp.

### Phase 4: Administrative Operations
- [ ] **TC-ADM-01:** Access Control: Attempt to visit `/upload_questions/` as a normal student; verify redirect to dashboard.
- [ ] **TC-ADM-02:** Staff Access: Log in as staff user; verify `/upload_questions/` form renders dropdown with all `MockTest` instances.
- [ ] **TC-ADM-03:** Valid Excel Ingestion: Upload a standard `.xlsx` file formatted with headers `Question`, `Option A`, `Option B`, `Option C`, `Option D`, `Answer`, `Explanation`. Verify questions are parsed and inserted into `accounts_question`.
- [ ] **TC-ADM-04:** Malformed Excel Ingestion: Upload an invalid `.xlsx` file missing header columns; verify form displays descriptive user error instead of 500 crash.

---

## 3. Recommended Automated Test Implementation Suite

To ensure stability prior to production, implement the following automated test suites using `pytest-django`:

```python
# accounts/tests/test_scoring.py (Example Target Structure)
import pytest
from accounts.models import Subject, MockTest, Question, TestResult

@pytest.mark.django_db
def test_standard_scoring_calculation(client, user):
    client.force_login(user)
    subject = Subject.objects.create(name="CAT")
    test = MockTest.objects.create(subject=subject, name="CAT Test 1")
    q1 = Question.objects.create(mock_test=test, question="Q1", option_a="1", option_b="2", correct_option="A")
    q2 = Question.objects.create(mock_test=test, question="Q2", option_a="1", option_b="2", correct_option="B")
    
    payload = {
        "answers": [0, 0], # Q1 correct (A), Q2 wrong (A instead of B)
        "question_times": [10, 15],
        "time_taken": 25
    }
    response = client.post(f"/submit-test/{test.id}/", payload, content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert data["correct"] == 1
    assert data["wrong"] == 1
    assert data["score"] == 2.0 # (1 * 3) - (1 * 1)
```

