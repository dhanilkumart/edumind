from operator import index
from unicodedata import category

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import MockTest, TestAttempt
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, request
from django.shortcuts import render, redirect
from django.conf import settings as django_settings

from .models import (
    MockTest,
    Question,
    TestResult,
    UserAnswer,
    Profile,
    Subject,
    MobileOTP
)

from .forms import ExcelUploadForm

import json
import random
from pathlib import Path

import openpyxl



from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Subject, MockTest

from django.http import Http404


def get_railway_subject():
    """
    Find the existing Railway or RRB subject.
    """
    subject = (
        Subject.objects.filter(name__iexact="RAILWAY").first()
        or Subject.objects.filter(name__iexact="RRB").first()
    )

    if subject is None:
        raise Http404(
            "Railway subject not found. Check the Subject table."
        )

    return subject


@login_required
def railway_categories(request):
    """
    Main page showing JE, ALP, NTPC and Group D.
    """
    return render(request, "railway.html")


@login_required
def rrb_je_categories(request):
    """
    Page showing RRB JE CBT Tier 1 and Tier 2.
    """
    return render(request, "rrb_je_categories.html")


@login_required
def railway_exam_tests(request, exam_type):
    """
    Show existing mock tests for the selected Railway exam.
    """

    exam_details = {
        "je-cbt-1": {
            "title": "RRB JE CBT Tier 1 Mock Tests",
            "search": ["RRB JE CBT 1", "RRB JE CBT Tier 1"],
        },
        "je-cbt-2": {
            "title": "RRB JE CBT Tier 2 Mock Tests",
            "search": ["RRB JE CBT 2", "RRB JE CBT Tier 2"],
        },
        "alp": {
            "title": "RRB ALP Mock Tests",
            "search": ["RRB ALP", "ALP"],
        },
        "ntpc": {
            "title": "RRB NTPC Mock Tests",
            "search": ["RRB NTPC", "NTPC"],
        },
        "group-d": {
            "title": "RRB Group D Mock Tests",
            "search": ["RRB Group D", "Group D"],
        },
    }

    details = exam_details.get(exam_type)

    if details is None:
        raise Http404("Railway exam category not found.")

    subject = get_railway_subject()

    # Match existing mock-test names without creating new tests.
    from django.db.models import Q

    name_filter = Q()

    for search_term in details["search"]:
        name_filter |= Q(name__icontains=search_term)

    mock_tests = (
        MockTest.objects.filter(
            subject=subject
        )
        .filter(name_filter)
        .prefetch_related("questions")
        .order_by("name")
        .distinct()
    )

    context = {
        "subject": subject,
        "exam_type": exam_type,
        "exam_title": details["title"],
        "mock_tests": mock_tests,
    }

    return render(
        request,
        "railway_exam_tests.html",
        context,
    )



def home(request):
    return render(
        request,
        "home.html"
    )

@login_required
def test_view(request, test_id):

    mock_test = get_object_or_404(
        MockTest,
        id=test_id
    )

    questions = Question.objects.filter(
        mock_test=mock_test
    ).order_by(
        "question_no",
        "id"
    )

    questions_data = []

    for question in questions:

        questions_data.append({
            "id": question.id,
            "question_no": question.question_no,
            "question": question.question,
            "options": [
                question.option_a,
                question.option_b,
                question.option_c,
                question.option_d,
            ],
            "correct_option": question.correct_option,
            "explanation": question.explanation or "",
        })

    return render(
        request,
        "test.html",
        {
            "mock_test": mock_test,
            "questions_json": json.dumps(
                questions_data
            ),
            "duration_minutes": mock_test.duration_minutes,
        }
    )



@login_required
def exams(request):

    # Get all mock tests
    mock_tests = MockTest.objects.select_related(
        "subject"
    ).all().order_by(
        "subject__name",
        "id"
    )

    # Tests already attempted by this user
    attempted_test_ids = set(
        TestResult.objects.filter(
            user=request.user,
            mock_test__isnull=False
        ).values_list(
            "mock_test_id",
            flat=True
        )
    )

    return render(
        request,
        "exams.html",
        {
            "mock_tests": mock_tests,
            "attempted_test_ids": attempted_test_ids,
        }
    )

@login_required
def dashboard(request):

    return render(
        request,
        "dashboard.html"
    )

def logout_view(request):
    logout(request)
    return redirect("home")

def mock_tests(request):
    subjects = Subject.objects.all().order_by("name")
    return render(
        request,
        "mock_tests.html",
        {
            "subjects": subjects,
        }
    )

@login_required
def performance(request):

    results = TestResult.objects.filter(
    user=request.user
).select_related(
    'mock_test'
).order_by('created_at')

    tests_attempted = results.count()

    for result in results:
        result.test_id = result.mock_test_id
    result.attempted = result.correct + result.wrong

    # -----------------------------
# TEST-SPECIFIC DATA
# -----------------------------
    for result in results:

        if result.mock_test:
            result.test_id = result.mock_test_id
        result.test_name = result.mock_test.name if result.mock_test else result.test_name
    else:
        result.test_id = None

    result.attempted = (
        int(result.correct or 0) +
        int(result.wrong or 0)
    )

    result.wrong = int(result.wrong or 0)

    result.unanswered = int(
        result.unanswered or 0
    )

    # -----------------------------
    # OVERALL STATISTICS
    # -----------------------------

    if tests_attempted > 0:

        total_score = sum(float(r.score or 0) for r in results)

        average_score = total_score / tests_attempted

        highest_score = max(
            float(r.score or 0) for r in results
        )

        total_correct = sum(
            int(r.correct or 0) for r in results
        )

        total_wrong = sum(
            int(r.wrong or 0) for r in results
        )

        total_unanswered = sum(
            int(r.unanswered or 0) for r in results
        )

        total_attempted = total_correct + total_wrong

        if total_attempted > 0:
            overall_accuracy = (
                total_correct / total_attempted
            ) * 100
        else:
            overall_accuracy = 0

    else:

        average_score = 0
        highest_score = 0
        total_correct = 0
        total_wrong = 0
        total_unanswered = 0
        overall_accuracy = 0

    # -----------------------------
    # DATA FOR SCORE BAR CHART
    # -----------------------------

    chart_labels = []
    chart_scores = []

    for index, result in enumerate(results, start=1):

        test_name = getattr(
            result,
            "test_name",
            None
        )

    if not test_name:
        if result.mock_test:
            test_name = str(result.mock_test.name if result.mock_test else result.test_name)
    else:
        test_name = str(result.test_name or "")
    
    chart_labels.append(
            f"Test {index}"
        )

    chart_scores.append(
            float(result.score or 0)
        )

    # -----------------------------
    # DATA FOR CATEGORY ANALYSIS
    # -----------------------------

    category_data = {
        "CAT": {
            "tests": 0,
            "score": 0,
            "correct": 0,
            "wrong": 0,
            "unanswered": 0,
        },
        "Bank": {
            "tests": 0,
            "score": 0,
            "correct": 0,
            "wrong": 0,
            "unanswered": 0,
        },
        "SSC": {
            "tests": 0,
            "score": 0,
            "correct": 0,
            "wrong": 0,
            "unanswered": 0,
        },
        "RRB": {
            "tests": 0,
            "score": 0,
            "correct": 0,
            "wrong": 0,
            "unanswered": 0,
        },
        "Others": {
            "tests": 0,
            "score": 0,
            "correct": 0,
            "wrong": 0,
            "unanswered": 0,
        },
    }

    # Try to identify category from the test/subject name
    for result in results:

      if result.mock_test:
        test_name = str(result.mock_test.name if result.mock_test else result.test_name)
    else:
        test_name = str(result.test_name or "")

    name_upper = test_name.upper()

    if "CAT" in name_upper:
        category = "CAT"

    elif "BANK" in name_upper:
        category = "Bank"

    elif "SSC" in name_upper:
        category = "SSC"

    elif "RAILWAY" in name_upper or "RRB" in name_upper:
        category = "RRB"

    else:
        category = "Others"

    category_data[category]["tests"] += 1
    category_data[category]["score"] += float(
        result.score or 0
    )
    category_data[category]["correct"] += int(
        result.correct or 0
    )
    category_data[category]["wrong"] += int(
        result.wrong or 0
    )
    category_data[category]["unanswered"] += int(
        result.unanswered or 0
    )


    # -----------------------------
    # CATEGORY CHART DATA
    # -----------------------------

    category_labels = list(category_data.keys())

    category_scores = [
        round(
            category_data[c]["score"] /
            category_data[c]["tests"], 2
        )
        if category_data[c]["tests"] > 0
        else 0
        for c in category_labels
    ]

    # -----------------------------
    # CONTEXT
    # -----------------------------

    context = {

        "results": results,

        "tests_attempted": tests_attempted,

        "average_score": round(
            average_score, 2
        ),

        "highest_score": round(
            highest_score, 2
        ),

        "total_correct": total_correct,

        "total_wrong": total_wrong,

        "total_unanswered": total_unanswered,

        "overall_accuracy": round(
            overall_accuracy, 2
        ),

        "chart_labels": chart_labels,

        "chart_scores": chart_scores,

        "category_labels": category_labels,

        "category_scores": category_scores,

        "category_data": category_data,
    }

    return render(
        request,
        "performance_analysis.html",
        context
    )

def previous_tests(request):

    if not request.user.is_authenticated:
        return redirect("login")

    print("LOGIN USER:", request.user.id, request.user.username)

    tests = TestResult.objects.filter(
        user=request.user
    ).order_by("-created_at")

    print("TEST COUNT:", tests.count())

    return render(
        request,
        "previous_tests.html",
        {
            "tests": tests,
        }
    )


def profile(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "profile.html",
        {
            "user": request.user,
        }
    )

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


def login_view(request):
    import re

    from django.contrib.auth import authenticate, login
    from django.contrib.auth.models import User
    from django.shortcuts import render, redirect
    from .models import Profile

    if request.method != "POST":
        return render(request, "login.html")

    identifier = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    remember_me = request.POST.get("remember_me")

    if not identifier:
        return render(request, "login.html", {
            "error": "Enter your User ID, email address, or mobile number."
        })

    if not password:
        return render(request, "login.html", {
            "error": "Please enter your password.",
            "username": identifier,
        })

    # 1. Try the registered username / User ID first.
    user_record = User.objects.filter(username=identifier).first()

    # 2. If not found, look up the registered email address.
    if user_record is None and "@" in identifier:
        email_matches = User.objects.filter(email__iexact=identifier)

        # Only use the email if it identifies exactly one account.
        if email_matches.count() == 1:
            user_record = email_matches.first()

    # 3. If not found, look up the registered mobile number.
    if user_record is None:
        digits = re.sub(r"\D", "", identifier)

        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]

        if re.fullmatch(r"[6-9]\d{9}", digits):
            profiles = Profile.objects.filter(
                mobile_number__in=[digits, "+91" + digits]
            ).select_related("user")

            if profiles.count() == 1:
                user_record = profiles.first().user

    # Authenticate with the actual username stored by Django.
    user = None

    if user_record is not None:
        user = authenticate(
            request,
            username=user_record.username,
            password=password,
        )

    if user is not None:
        login(request, user)

        if remember_me:
            request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            request.session.set_expiry(0)

        return redirect("dashboard")

    return render(request, "login.html", {
        "error": (
            "Login failed. Check your registered User ID, email or "
            "mobile number and password. If you forgot your password, "
            "use the Forgot password link."
        ),
        "username": identifier,
    })

def register(request):
    import re
    import secrets

    from django.contrib.auth.models import User
    from django.db import transaction
    from django.shortcuts import render, redirect

    from .models import Profile, MobileOTP

    template_name = "register.html"

    if request.method != "POST":
        return render(request, template_name)

    # Read form fields
    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip().lower()
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    mobile_number = request.POST.get("mobile_number", "").strip()
    password = request.POST.get("password", "")
    password2 = request.POST.get("password2", "")

    form_data = request.POST

    def registration_error(message):
        return render(
            request,
            template_name,
            {
                "error": message,
                "form_data": form_data,
            },
        )

    # Required fields
    if not all([
        username,
        email,
        first_name,
        last_name,
        mobile_number,
        password,
        password2,
    ]):
        return registration_error("Please fill in all required fields.")

    # Username validation
    if len(username) < 8:
        return registration_error(
            "Username must contain at least 8 characters."
        )

    if not re.fullmatch(r"[A-Za-z0-9_]+", username):
        return registration_error(
            "Username may contain only letters, numbers and underscores."
        )

    if User.objects.filter(username__iexact=username).exists():
        return registration_error(
            "Username already exists. Please choose another."
        )

    # Email validation
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError

    try:
        validate_email(email)
    except ValidationError:
        return registration_error("Please enter a valid email address.")

    if User.objects.filter(email__iexact=email).exists():
        return registration_error(
            "This email address is already registered."
        )

    # Mobile validation: Indian mobile number
    digits = re.sub(r"\D", "", mobile_number)

    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]

    if not re.fullmatch(r"[6-9]\d{9}", digits):
        return registration_error(
            "Enter a valid 10-digit Indian mobile number."
        )

    mobile_number = digits

    if Profile.objects.filter(mobile_number=mobile_number).exists():
        return registration_error(
            "This mobile number is already registered."
        )

    # Password validation
    if len(password) < 8:
        return registration_error(
            "Password must contain at least 8 characters."
        )

    if not re.search(r"[A-Za-z]", password):
        return registration_error(
            "Password must contain at least one letter."
        )

    if not re.search(r"\d", password):
        return registration_error(
            "Password must contain at least one number."
        )

    if not re.search(r"[^A-Za-z0-9]", password):
        return registration_error(
            "Password must contain at least one special character."
        )

    if password != password2:
        return registration_error(
            "Password and confirmation password do not match."
        )
# Create the inactive account and OTP
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=False,
            )

            profile = Profile.objects.get(user=user)
            profile.mobile_number = mobile_number
            profile.save(update_fields=["mobile_number"])

            # Invalidate earlier OTPs for this user
            MobileOTP.objects.filter(user=user).delete()

            otp = f"{secrets.randbelow(900000) + 100000}"

            MobileOTP.objects.create(
                user=user,
                otp=otp,
            )

    except Exception:
        import logging
        logging.exception("EduMind registration failed")
        return registration_error(
            "Registration could not be completed. "
            "Please check the Django terminal for the exact error."
        )

    # Development only: OTP appears in the runserver terminal.
    # This does NOT send an SMS.
    if getattr(
        __import__("django.conf", fromlist=["settings"]).settings,
        "DEBUG",
        False,
    ):
        print(f"EduMind development OTP for {username}: {otp}")

    request.session["otp_user_id"] = user.id

    return redirect("verify_password_otp")

def verify_legacy_email_otp(request):
    from django.contrib.auth.models import User
    from .models import MobileOTP

    user_id = request.session.get("otp_user_id")

    if not user_id:
        return redirect("register")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("register")

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        otp_record = MobileOTP.objects.filter(
            user=user,
            otp=entered_otp,
            is_verified=False
        ).order_by("-created_at").first()

        if otp_record:
            otp_record.is_verified = True
            otp_record.save()

            user.is_active = True
            user.save()

            del request.session["otp_user_id"]

            return redirect("login")

        return render(
            request,
            "verify_password_otp.html",
            {
                "error": "Invalid OTP. Please enter the correct 6-digit OTP."
            }
        )

    return render(request, "verify_password_otp.html")

def result_detail(request, test_id):
    if not request.user.is_authenticated:
        return redirect("login")

    test = get_object_or_404(
        TestResult,
        id=test_id,
        user=request.user
    )

    answers = UserAnswer.objects.filter(
        test_result=test
    ).select_related("question")


    return render(
        request,
        "result_detail.html",
        {
            "test": test,
            "answers": answers,
        }
    )

def review(request):

    review_data = request.session.get("review_data", [])

    review_questions = []

    for item in review_data:

        question = Question.objects.get(id=item["question_id"])

        review_questions.append({
            "question": question,
            "selected_answer": item["selected_answer"],
            "correct_answer": question.correct_option,
        })

    return render(
        request,
        "review.html",
        {
            "review_questions": review_questions,
        }
    )

@login_required
def review_test(request, test_id, question_no=1):

    # --------------------------------------------------
    # Get the attempted test
    # --------------------------------------------------

    test = get_object_or_404(
        TestResult,
        id=test_id,
        user=request.user
    )

    # --------------------------------------------------
    # Get all answers belonging to this test
    # --------------------------------------------------

    answers = list(
        UserAnswer.objects
        .filter(test_result=test)
        .select_related("question")
        .order_by("question__question_no", "id")
    )

    total_questions = len(answers)

    # --------------------------------------------------
    # No answers saved
    # --------------------------------------------------

    if total_questions == 0:

        return render(
            request,
            "review_test.html",
            {
                "test": test,
                "answer": None,
                "question_no": 0,
                "total_questions": 0,
                "previous_question": None,
                "next_question": None,
                "answers": [],
            },
        )

    # --------------------------------------------------
    # Keep question number within range
    # --------------------------------------------------

    question_no = max(
        1,
        min(question_no, total_questions)
    )

    # --------------------------------------------------
    # Current answer
    # --------------------------------------------------

    answer = answers[question_no - 1]

    # --------------------------------------------------
    # Convert numeric answer to A/B/C/D
    #
    # 1 → A
    # 2 → B
    # 3 → C
    # 4 → D
    #
    # If the database already contains A/B/C/D,
    # leave it unchanged.
    # --------------------------------------------------

    option_map = {
        "1": "A",
        "2": "B",
        "3": "C",
        "4": "D",
    }

    if answer.selected_option:

        selected = str(
            answer.selected_option
        ).strip().upper()

        selected = option_map.get(
            selected,
            selected
        )

    else:

        selected = ""

    # --------------------------------------------------
    # Correct answer
    # --------------------------------------------------

    correct = str(
        answer.question.correct_option
    ).strip().upper()

    # --------------------------------------------------
    # Calculate correctness
    # --------------------------------------------------

    is_correct = (
        bool(selected)
        and selected == correct
    )

    # --------------------------------------------------
    # Send display values to template
    # --------------------------------------------------

    return render(
        request,
        "review_test.html",
        {
            "test": test,

            "answer": answer,

            # Display values used by review page
            "selected_option": selected,
            "correct_option": correct,
            "is_correct": is_correct,

            "answers": answers,

            "question_no": question_no,

            "total_questions": total_questions,

            "previous_question": (
                question_no - 1
                if question_no > 1
                else None
            ),

            "next_question": (
                question_no + 1
                if question_no < total_questions
                else None
            ),
        },
    )

def settings_view(request):
    return render(request, "settings.html")

@login_required
def subjects(request):
    all_subjects = Subject.objects.all()

    return render(
        request,
        "subjects.html",
        {
            "subjects": all_subjects,
            "show_olympiad": True,
        },
    )

@login_required
def subject_mock_tests(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    if subject_id == 2:
        return redirect('banking')

    if subject_id == 5:
        return redirect('railway')

    if subject_id == 13:
        return redirect('olympiad')

    mock_tests = list(
        MockTest.objects.filter(subject=subject).prefetch_related("questions")
    )

    attempted_test_ids = set(
        TestResult.objects.filter(
            user=request.user,
            mock_test__isnull=False
        ).values_list("mock_test_id", flat=True)
    )

    # CAT groups — preserve the existing CAT functionality.
    full_tests = []
    qa_tests = []
    reasoning_tests = []
    english_tests = []
    other_tests = []

    # Banking categories.
    bank_categories = [
        {
            "name": "SBI Assistant",
            "keywords": ("sbi assistant", "sbi clerk", "sbi junior associate"),
            "tests": [],
        },
        {
            "name": "SBI PO",
            "keywords": ("sbi po", "sbi probationary officer"),
            "tests": [],
        },
        {
            "name": "IBPS Assistant",
            "keywords": (
                "ibps assistant", "ibps clerk",
                "ibps customer service associate",
            ),
            "tests": [],
        },
        {
            "name": "IBPS PO",
            "keywords": ("ibps po", "ibps probationary officer"),
            "tests": [],
        },
        {
            "name": "RRB Assistant",
            "keywords": (
                "rrb assistant", "rrb office assistant",
                "regional rural bank assistant",
            ),
            "tests": [],
        },
        {
            "name": "RRB PO",
            "keywords": (
                "rrb po", "rrb officer scale i",
                "rrb officer scale 1",
            ),
            "tests": [],
        },
    ]

    unassigned_bank_tests = []

    if subject.name.strip().upper() == "CAT":
        for test in mock_tests:
            name = test.name.strip().lower()

            if "full mock test" in name:
                full_tests.append(test)
            elif (
                "qa session test" in name
                or "qa sessions test" in name
                or "sessions test qa" in name
            ):
                qa_tests.append(test)
            elif (
                "reasoning session test" in name
                or "reasoning sessions test" in name
                or "sessions test reasoning" in name
            ):
                reasoning_tests.append(test)
            elif (
                "english session test" in name
                or "english sessions test" in name
                or "sessions test english" in name
            ):
                english_tests.append(test)
            else:
                other_tests.append(test)

    elif subject.name.strip().upper() in ("BANK", "BANKING"):
        assigned_ids = set()

        for test in mock_tests:
            name = test.name.strip().lower()
            matched = False

            for category in bank_categories:
                if any(keyword in name for keyword in category["keywords"]):
                    category["tests"].append(test)
                    assigned_ids.add(test.id)
                    matched = True
                    break

            if not matched:
                unassigned_bank_tests.append(test)

        # Ten slots per category. Empty slots will show Available Soon.
        for category in bank_categories:
            category["slots"] = []

            for number in range(1, 11):
                test = (
                    category["tests"][number - 1]
                    if number <= len(category["tests"])
                    else None
                )

                category["slots"].append({
                    "number": number,
                    "test": test,
                })

    else:
        other_tests = mock_tests

    session_test_count = (
        len(qa_tests)
        + len(reasoning_tests)
        + len(english_tests)
    )

    

    return render(
        request,
        "subject_mock_tests.html",
        {
            "subject": subject,
            "mock_tests": mock_tests,
            "attempted_test_ids": attempted_test_ids,
            "full_tests": full_tests,
            "qa_tests": qa_tests,
            "reasoning_tests": reasoning_tests,
            "english_tests": english_tests,
            "other_tests": other_tests,
            "session_test_count": session_test_count,
            "bank_categories": bank_categories,
            "unassigned_bank_tests": unassigned_bank_tests,
        },
    )

@login_required
def cat_full_mock_tests(request):

    cat_subject = get_object_or_404(
        Subject,
        name__iexact="CAT"
    )

    full_tests = list(
        MockTest.objects.filter(
            subject=cat_subject,
            name__icontains="Full Mock Test"
        ).prefetch_related("questions")
    )

    # Sort by test name/number
    full_tests.sort(key=lambda test: test.name)

    attempted_test_ids = set(
        TestResult.objects.filter(
            user=request.user,
            mock_test__in=full_tests
        ).values_list(
            "mock_test_id",
            flat=True
        )
    )

    return render(
        request,
        "cat_full_mock_tests.html",
        {
            "subject": cat_subject,
            "full_tests": full_tests,
            "attempted_test_ids": attempted_test_ids,
        }
    )


@login_required
def cat_session_tests(request):

    cat_subject = get_object_or_404(
        Subject,
        name__iexact="CAT"
    )

    mock_tests = list(
        MockTest.objects.filter(
            subject=cat_subject
        ).prefetch_related("questions")
    )

    qa_tests = []
    reasoning_tests = []
    english_tests = []

    for test in mock_tests:

        name = test.name.strip().lower()

        if "qa session test" in name:
            qa_tests.append(test)

        elif "reasoning session test" in name:
            reasoning_tests.append(test)

        elif "english session test" in name:
            english_tests.append(test)

    qa_tests.sort(key=lambda test: test.name)
    reasoning_tests.sort(key=lambda test: test.name)
    english_tests.sort(key=lambda test: test.name)

    all_session_tests = (
        qa_tests +
        reasoning_tests +
        english_tests
    )

    attempted_test_ids = set(
        TestResult.objects.filter(
            user=request.user,
            mock_test__in=all_session_tests
        ).values_list(
            "mock_test_id",
            flat=True
        )
    )

    return render(
        request,
        "cat_session_tests.html",
        {
            "subject": cat_subject,

            "qa_tests": qa_tests,
            "reasoning_tests": reasoning_tests,
            "english_tests": english_tests,

            "attempted_test_ids": attempted_test_ids,
        }
    )

# =========================================================
# BANKING EXAM PAGES
# =========================================================


@login_required
def bank_exam_tests(request, exam_key):
    bank_exams = {
        "sbi-po": {
            "title": "SBI PO",
            "keywords": ["sbi po", "sbi probationary officer"],
        },
        "sbi-clerk": {
            "title": "SBI Assistant",
            "keywords": [
                "sbi clerk",
                "sbi assistant",
                "sbi junior associate",
            ],
        },
        "ibps-po": {
            "title": "IBPS PO",
            "keywords": ["ibps po", "ibps probationary officer"],
        },
        "ibps-clerk": {
            "title": "IBPS Assistant",
            "keywords": ["ibps clerk", "ibps assistant"],
        },
        "rrb-po": {
            "title": "RRB PO",
            "keywords": ["rrb po", "rrb officer scale i"],
        },
        "rrb-office-assistant": {
            "title": "RRB Assistant",
            "keywords": ["rrb office assistant", "rrb assistant"],
        },
        "rbi-grade-b": {
            "title": "RBI Grade B",
            "keywords": ["rbi grade b"],
        },
        "rbi-assistant": {
            "title": "RBI Assistant",
            "keywords": ["rbi assistant"],
        },
    }

    exam = bank_exams.get(exam_key)

    if exam is None:
        raise Http404("Bank exam not found")

    bank_subject = get_object_or_404(
        Subject,
        name__iexact="BANK",
    )

    all_tests = MockTest.objects.filter(
        subject=bank_subject
    ).prefetch_related("questions").order_by("name", "id")

    matching_tests = [
        test for test in all_tests
        if any(
            keyword in test.name.lower()
            for keyword in exam["keywords"]
        )
    ][:10]

    attempted_test_ids = set(
        TestResult.objects.filter(
            user=request.user,
            mock_test__isnull=False,
        ).values_list("mock_test_id", flat=True)
    )

    slots = [
        {
            "number": number,
            "test": (
                matching_tests[number - 1]
                if number <= len(matching_tests)
                else None
            ),
        }
        for number in range(1, 11)
    ]

    return render(
        request,
        "bank_exam_tests.html",
        {
            "exam": exam,
            "slots": slots,
            "attempted_test_ids": attempted_test_ids,
        },
    )


@login_required
def ibps_po(request):
    return render(
        request,
        "exams/banking/ibps_po.html"
    )


@login_required
def ibps_clerk(request):
    return render(
        request,
        "exams/banking/ibps_clerk.html"
    )


@login_required
def sbi_po(request):
    return render(
        request,
        "exams/banking/sbi_po.html"
    )


@login_required
def sbi_clerk(request):
    return render(
        request,
        "exams/banking/sbi_clerk.html"
    )


@login_required
def rrb_po(request):
    return render(
        request,
        "exams/banking/rrb_po.html"
    )


@login_required
def rrb_office_assistant(request):
    return render(
        request,
        "exams/banking/rrb_office_assistant.html"
    )


@login_required
def rbi_grade_b(request):
    return render(
        request,
        "exams/banking/rbi_grade_b.html"
    )


@login_required
def rbi_assistant(request):
    return render(
        request,
        "exams/banking/rbi_assistant.html"
    )


# =========================================================
# SSC EXAM PAGES
# =========================================================

@login_required
def ssc_cgl(request):
    subject = get_object_or_404(
        Subject,
        name__iexact="SSC"
    )

    mock_tests = MockTest.objects.filter(
        subject=subject,
        name__in=[
            "Mock Test 1",
            "Mock Test 2",
            "Mock Test 3",
        ]
    ).order_by("name")

    return render(
        request,
        "exams/ssc/ssc_cgl.html",
        {"mock_tests": mock_tests}
    )


@login_required
def ssc_chsl(request):
    subject = get_object_or_404(
        Subject,
        name__iexact="SSC"
    )

    mock_tests = MockTest.objects.filter(
        subject=subject,
        name__icontains="CHSL"
    ).order_by("id")

    return render(
        request,
        "exams/ssc/ssc_chsl.html",
        {"mock_tests": mock_tests}
    )

@login_required
def ssc_je(request):
    subject = get_object_or_404(
        Subject,
        name__iexact="SSC"
    )

    mock_tests = MockTest.objects.filter(
        subject=subject,
        name__in=[
            "Mock Test 1",
            "Mock Test 2",
            "Mock Test 3",
        ]
    ).order_by("name")

    return render(
        request,
        "exams/ssc/ssc_je.html",
        {"mock_tests": mock_tests}
    )   



@login_required
def ssc_mts(request):
    subject = get_object_or_404(
        Subject,
        name__iexact="SSC"
    )

    mock_tests = MockTest.objects.filter(
        subject=subject,
        name__in=[
            "Mock Test 1",
            "Mock Test 2",
            "Mock Test 3",
        ]
    ).order_by("name")

    return render(
        request,
        "exams/ssc/ssc_mts.html"
    )


@login_required
def ssc_gd(request):
    return render(
        request,
        "exams/ssc/ssc_gd.html"
    )


@login_required
def ssc_cpo(request):
    return render(
        request,
        "exams/ssc/ssc_cpo.html"
    )


@login_required
def ssc_stenographer(request):
    return render(
        request,
        "exams/ssc/ssc_stenographer.html"
    )


# =========================================================
# RAILWAY / RRB EXAM PAGES
# =========================================================

@login_required
def rrb_je_cbt1_mock_tests(request):

    railway_subject = (
        Subject.objects.filter(name__iexact="RAILWAY").first()
        or Subject.objects.filter(name__iexact="RRB").first()
    )

    if railway_subject is None:
        raise Http404("Railway/RRB subject not found.")

    # Include tests even when questions are not uploaded.
    cbt1_tests = list(
        MockTest.objects.filter(
            subject=railway_subject,
            name__icontains="CBT",
        ).prefetch_related("questions").distinct()
    )

    cbt1_tests.sort(key=lambda test: test.name)

    # Determine availability using the actual question count.
    for test in cbt1_tests:
        test.question_count = len(test.questions.all())
        test.is_available = test.question_count > 0

    attempted_test_ids = set(
        TestResult.objects.filter(
            user=request.user,
            mock_test__in=cbt1_tests,
        ).values_list("mock_test_id", flat=True)
    )

    return render(
        request,
        "rrb_je_cbt1_mock_tests.html",
        {
            "subject": railway_subject,
            "cbt1_tests": cbt1_tests,
            "attempted_test_ids": attempted_test_ids,
            "total_tests": len(cbt1_tests),
        }
    )


@login_required
def rrb_alp(request):

    railway_subject = Subject.objects.filter(
        name__iexact="RAILWAY"
    ).first()

    uploaded_tests = {}

    if railway_subject:
        tests = (
            MockTest.objects.filter(
                subject=railway_subject,
                name__icontains="ALP",
            )
            .prefetch_related("questions")
        )

        for test in tests:
            uploaded_tests[test.name.strip().lower()] = test

    attempted_test_ids = set(
        TestResult.objects.filter(
            user=request.user,
            mock_test__isnull=False,
        ).values_list("mock_test_id", flat=True)
    )

    alp_tests = []

    for i in range(1, 11):

        # Match the actual database name
        database_name = f"ALP Test - {i}".lower()

        uploaded_test = uploaded_tests.get(database_name)

        question_count = (
            uploaded_test.questions.count()
            if uploaded_test else 0
        )

        alp_tests.append({
            "name": f"RRB ALP Test - {i}",
            "number": i,
            "mock_test": uploaded_test,
            "question_count": question_count,
            "available": question_count > 0,
            "attempted": (
                uploaded_test.id in attempted_test_ids
                if uploaded_test else False
            ),
        })

    return render(
        request,
        "railway_assistant_loco_piolet.html",
        {
            "alp_tests": alp_tests,
        }
    )

@login_required
def rrb_ntpc(request):
    return render(
        request,
        "exams/railway/rrb_ntpc.html"
    )


@login_required
def rrb_group_d(request):
    return render(
        request,
        "exams/railway/rrb_group_d.html"
    )


@login_required
def submit_test(request, mock_test_id):

    if request.method != "POST":
        return redirect(
            "test",
            mock_test_id=mock_test_id
        )


    mock_test = get_object_or_404(
        MockTest,
        id=mock_test_id
    )


    questions = Question.objects.filter(
        mock_test=mock_test
    ).order_by("id")


    # =====================================================
    # GET DATA SENT FROM JAVASCRIPT
    # =====================================================

    data = json.loads(
        request.body
    )


    answers = data.get(
        "answers",
        []
    )


    question_times = data.get(
        "question_times",
        []
    )


    time_taken = int(
        data.get(
            "time_taken",
            0
        )
    )


    # =====================================================
    # TOTAL QUESTIONS
    # =====================================================

    total_questions = questions.count()


    # =====================================================
    # INITIALIZE COUNTERS
    # =====================================================

    correct = 0

    wrong = 0

    unanswered = 0


    # =====================================================
    # CREATE TEST RESULT
    # =====================================================

    test_result = TestResult.objects.create(

        user=request.user,

        mock_test=mock_test,

        test_name=mock_test.name,

        total_questions=total_questions,

        correct=0,

        wrong=0,

        unanswered=0,

        score=0,

        accuracy=0,

        time_taken=time_taken,

    )


    # =====================================================
    # OPTION INDEX → LETTER
    #
    # JavaScript sends:
    #
    # 0 = A
    # 1 = B
    # 2 = C
    # 3 = D
    # =====================================================

    option_letters = [
        "A",
        "B",
        "C",
        "D"
    ]


    # =====================================================
    # PROCESS EVERY QUESTION
    # =====================================================

    for index, question in enumerate(
        questions
    ):

        selected_option = ""


        # -------------------------------------------------
        # GET USER ANSWER
        # -------------------------------------------------

        if index < len(answers):

            answer = answers[index]


            if (
                answer is not None
                and answer != ""
            ):

                # -----------------------------------------
                # IF JAVASCRIPT SENT 0 / 1 / 2 / 3
                # -----------------------------------------

                if isinstance(
                    answer,
                    int
                ):

                    if (
                        0 <= answer < 4
                    ):

                        selected_option = (
                            option_letters[answer]
                        )


                # -----------------------------------------
                # JAVASCRIPT MAY SEND STRING "0"/"1"/"2"/"3"
                # -----------------------------------------

                elif str(
                    answer
                ).strip() in [
                    "0",
                    "1",
                    "2",
                    "3"
                ]:

                    selected_option = (
                        option_letters[
                            int(
                                str(answer).strip()
                            )
                        ]
                    )


                # -----------------------------------------
                # ALSO ACCEPT A/B/C/D
                # -----------------------------------------

                else:

                    possible_letter = str(
                        answer
                    ).strip().upper()


                    if possible_letter in [
                        "A",
                        "B",
                        "C",
                        "D"
                    ]:

                        selected_option = (
                            possible_letter
                        )


        # =================================================
        # CHECK ANSWER
        # =================================================

        if selected_option == "":

            unanswered += 1

            is_correct = False


        else:

            correct_option = str(
                question.correct_option
            ).strip().upper()


            if (
                selected_option
                == correct_option
            ):

                correct += 1

                is_correct = True


            else:

                wrong += 1

                is_correct = False


        # =================================================
        # TIME SPENT ON QUESTION
        # =================================================

        time_spent = 0


        if index < len(
            question_times
        ):

            try:

                time_spent = int(
                    question_times[index]
                )

            except (
                TypeError,
                ValueError
            ):

                time_spent = 0


        # =================================================
        # SAVE USER ANSWER
        # =================================================

        UserAnswer.objects.create(

            test_result=test_result,

            question=question,

            selected_option=selected_option,

            is_correct=is_correct,

            time_spent=time_spent,

        )


    

    # =====================================================
    # CALCULATE SCORE
    # =====================================================

    if "ALP" in mock_test.name.upper():

    # RRB ALP: +1 for correct, -1/3 for wrong
        score = (
        correct - (wrong / 3)
    )
    else:

    # Preserve existing scoring for all other tests

        score = (
            (correct * 3)
            -
            (wrong * 1)
        )

    # =====================================================
    # ATTEMPTED
    # =====================================================

    attempted = (
        correct
        +
        wrong
    )


    # =====================================================
    # ACCURACY
    # =====================================================

    if attempted > 0:

        accuracy = (
            correct
            /
            attempted
        ) * 100

    else:

        accuracy = 0


    # =====================================================
    # UPDATE TEST RESULT
    # =====================================================

    test_result.correct = correct

    test_result.wrong = wrong

    test_result.unanswered = unanswered

    test_result.score = score

    test_result.accuracy = accuracy

    test_result.save()


    # =====================================================
    # SAVE TEST ATTEMPT
    # =====================================================

    TestAttempt.objects.create(

        user=request.user,

        mock_test=mock_test,

        score=score,

        total_questions=total_questions

    )


    # =====================================================
    # SEND RESULT TO JAVASCRIPT
    # =====================================================

    return JsonResponse({

        "success": True,

        "result_id":
            test_result.id,

        "total_questions":
            total_questions,

        "correct":
            correct,

        "wrong":
            wrong,

        "unanswered":
            unanswered,

        "score":
            score,

        "accuracy":
            round(
                accuracy,
                2
            ),

    })


@login_required
def upload_questions(request):

    if not request.user.is_staff:
        return redirect("dashboard")

    if request.method == "POST":

        form = ExcelUploadForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            mock_test = form.cleaned_data["mock_test"]
            excel_file = form.cleaned_data["excel_file"]

            workbook = openpyxl.load_workbook(
                excel_file,
                data_only=True
            )

            sheet = workbook.active

            uploaded_count = 0

            # =========================================================
            # READ HEADER ROW
            # =========================================================

            headers = list(
                sheet.iter_rows(
                    min_row=1,
                    max_row=1,
                    values_only=True
                )
            )[0]

            headers = [
                str(h).strip().lower()
                if h is not None
                else ""
                for h in headers
            ]

            # =========================================================
            # FIND QUESTION COLUMN
            # =========================================================

            question_headers = [
                "question",
                "question text",
                "question_text",
                "questions",
                "question statement",
                "question_statement"
            ]

            question_col = None

            for header in question_headers:

                if header in headers:

                    question_col = headers.index(header)
                    break

            if question_col is None:

                return HttpResponse(
                    "Excel file must contain a Question column. "
                    "Accepted headers: Question, Question Text, "
                    "Question_Text, Questions, Question Statement."
                )

            # =========================================================
            # FIND OPTION COLUMNS
            # =========================================================

            option_sets = [
                (
                    "option a",
                    "option b",
                    "option c",
                    "option d"
                ),
                (
                    "choice a",
                    "choice b",
                    "choice c",
                    "choice d"
                )
            ]

            option_a_col = None
            option_b_col = None
            option_c_col = None
            option_d_col = None

            for option_set in option_sets:

                if all(
                    option in headers
                    for option in option_set
                ):

                    option_a_col = headers.index(
                        option_set[0]
                    )

                    option_b_col = headers.index(
                        option_set[1]
                    )

                    option_c_col = headers.index(
                        option_set[2]
                    )

                    option_d_col = headers.index(
                        option_set[3]
                    )

                    break

            if option_a_col is None:

                return HttpResponse(
                    "Excel file must contain either "
                    "Option A-D or Choice A-D."
                )

            # =========================================================
            # FIND CORRECT ANSWER COLUMN
            # =========================================================

            answer_headers = [
                "correct answer",
                "correct_answer",
                "correct option",
                "correct_option",
                "answer",
                "correct"
            ]

            answer_col = None

            for header in answer_headers:

                if header in headers:

                    answer_col = headers.index(header)
                    break

            if answer_col is None:

                return HttpResponse(
                    "Excel file must contain a Correct Answer "
                    "or Correct Option column."
                )

            # =========================================================
            # FIND EXPLANATION COLUMN
            # =========================================================

            explanation_headers = [
                "explanation",
                "solution",
                "answer explanation",
                "answer_explanation"
            ]

            explanation_col = None

            for header in explanation_headers:

                if header in headers:

                    explanation_col = headers.index(header)
                    break

            # =========================================================
            # DETERMINE MAXIMUM REQUIRED COLUMN
            # =========================================================

            required_columns = [
                question_col,
                option_a_col,
                option_b_col,
                option_c_col,
                option_d_col,
                answer_col
            ]

            if explanation_col is not None:
                required_columns.append(
                    explanation_col
                )

            max_required_col = max(
                required_columns
            )

            # =========================================================
            # READ QUESTIONS
            # =========================================================

            for row in sheet.iter_rows(
                min_row=2,
                values_only=True
            ):

                row = list(row)

                # Make sure row is long enough
                while len(row) <= max_required_col:
                    row.append(None)

                # -----------------------------------------------------
                # QUESTION
                # -----------------------------------------------------

                question_text = row[question_col]

                if question_text is None:
                    continue

                question_text = str(
                    question_text
                ).strip()

                if not question_text:
                    continue

                # -----------------------------------------------------
                # OPTIONS
                # -----------------------------------------------------

                option_a = str(
                    row[option_a_col] or ""
                ).strip()

                option_b = str(
                    row[option_b_col] or ""
                ).strip()

                option_c = str(
                    row[option_c_col] or ""
                ).strip()

                option_d = str(
                    row[option_d_col] or ""
                ).strip()

                # -----------------------------------------------------
                # CORRECT ANSWER
                # -----------------------------------------------------

                correct_answer = str(
                    row[answer_col] or ""
                ).strip()

                # -----------------------------------------------------
                # EXPLANATION
                # -----------------------------------------------------

                if explanation_col is not None:

                    explanation = str(
                        row[explanation_col] or ""
                    ).strip()

                else:

                    explanation = ""

                # =====================================================
                # DETERMINE CORRECT OPTION
                # =====================================================

                correct_answer_upper = (
                    correct_answer.upper()
                )

                if correct_answer_upper in [
                    "A",
                    "B",
                    "C",
                    "D"
                ]:

                    correct_option = (
                        correct_answer_upper
                    )

                elif (
                    correct_answer.lower()
                    == option_a.lower()
                ):

                    correct_option = "A"

                elif (
                    correct_answer.lower()
                    == option_b.lower()
                ):

                    correct_option = "B"

                elif (
                    correct_answer.lower()
                    == option_c.lower()
                ):

                    correct_option = "C"

                elif (
                    correct_answer.lower()
                    == option_d.lower()
                ):

                    correct_option = "D"

                else:

                    # Skip rows where the correct answer
                    # cannot be identified
                    continue

                # =====================================================
                # CREATE QUESTION
                # =====================================================

                Question.objects.create(
                    mock_test=mock_test,
                    question=question_text,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_option=correct_option,
                    explanation=explanation
                )

                uploaded_count += 1

            # =========================================================
            # SUCCESS MESSAGE
            # =========================================================

            return HttpResponse(
                f"{uploaded_count} questions uploaded "
                f"successfully to "
                f"{mock_test.subject.name} - "
                f"{mock_test.name}."
            )

    else:

        form = ExcelUploadForm()

    return render(
        request,
        "upload_questions.html",
        {
            "form": form,
        }
    )

@login_required
def cat(request):
    return render(request, "cat.html")

@login_required
def cat_full_mock_tests(request):

    subject = get_object_or_404(
        Subject,
        name__iexact="CAT"
    )

    full_tests = (
        MockTest.objects
        .filter(
            subject=subject,
            name__icontains="Full Mock Test"
        )
        .prefetch_related("questions")
        .order_by("id")
    )

    attempted_test_ids = set(
        TestResult.objects.filter(
            user=request.user,
            mock_test__in=full_tests
        ).values_list(
            "mock_test_id",
            flat=True
        )
    )

    return render(
        request,
        "cat_full_mock_tests.html",
        {
            "subject": subject,
            "full_tests": full_tests,
            "attempted_test_ids": attempted_test_ids,
        }
    )

@login_required
def cat_session_tests(request):

    subject = get_object_or_404(
        Subject,
        name__iexact="CAT"
    )

    session_tests = (
        MockTest.objects
        .filter(
            subject=subject
        )
        .prefetch_related("questions")
        .order_by("id")
    )

    qa_tests = []
    reasoning_tests = []
    english_tests = []

    for test in session_tests:

        name = test.name.strip().lower()

        # ---------------------------------------------
        # QUANTITATIVE APTITUDE
        # ---------------------------------------------

        if (
            "qa session test" in name
            or "qa sessions test" in name
            or "sessions test qa" in name
        ):
            qa_tests.append(test)

        # ---------------------------------------------
        # REASONING
        # ---------------------------------------------

        elif (
            "reasoning session test" in name
            or "reasoning sessions test" in name
            or "sessions test reasoning" in name
        ):
            reasoning_tests.append(test)

        # ---------------------------------------------
        # ENGLISH
        # ---------------------------------------------

        elif (
            "english session test" in name
            or "english sessions test" in name
            or "sessions test english" in name
        ):
            english_tests.append(test)

    attempted_test_ids = set(
        TestResult.objects.filter(
            user=request.user,
            mock_test__in=session_tests
        ).values_list(
            "mock_test_id",
            flat=True
        )
    )

    return render(
        request,
        "cat_session_tests.html",
        {
            "subject": subject,

            "qa_tests": qa_tests,
            "reasoning_tests": reasoning_tests,
            "english_tests": english_tests,

            "attempted_test_ids": attempted_test_ids,
        }
    )

def banking(request):
    return render(request, "banking.html")


def ssc(request):
    return render(request, "ssc.html")


def railway(request):
    return render(request, "railway.html")


def tenth_pass(request):
    return render(request, "10th_pass.html")


def twelfth_pass(request):
    return render(request, "12th_pass.html")


def graduate(request):
    return render(request, "graduate.html")


def engineering(request):
    return render(request, "engineering.html")


def specialized(request):
    return render(request, "specialized.html")


@login_required
def olympiad_class(request, class_no):
    if class_no < 1 or class_no > 10:
        raise Http404("Class not found")

    subjects = [
        "Mathematics",
        "Physics",
        "Chemistry",
        "Biology",
        "History",
        "Geography",
    ]

    return render(
        request,
        "olympiad_subjects.html",
        {
            "class_no": class_no,
            "subjects": subjects,
        }
    )

@login_required
def category_performance(request, category):

    category_upper = category.upper()

    # =========================================================
    # ALL RESULTS OF CURRENT USER
    # =========================================================

    results = TestResult.objects.filter(
        user=request.user,
        mock_test__isnull=False
    ).select_related(
        "mock_test",
        "mock_test__subject"
    ).order_by(
        "created_at"
    )

    category_results = []

    for result in results:

        if not result.mock_test:
            continue

        mock_test = result.mock_test

        name = mock_test.name.upper()
        subject_name = mock_test.subject.name.upper()

        matched = False

        # =====================================================
        # CAT
        # =====================================================

        if category_upper == "CAT":

            matched = (
                "CAT" in subject_name
                or "CAT" in name
                or "QA SESSION TEST" in name
                or "REASONING SESSION TEST" in name
                or "ENGLISH SESSION TEST" in name
            )

        # =====================================================
        # BANK
        # =====================================================

        elif category_upper == "BANK":

            matched = (
                "BANK" in subject_name
                or "BANK" in name
                or "IBPS PO" in name
                or "SBI PO" in name
                or "RRB PO" in name
                or "IBPS CLERK" in name
                or "SBI CLERK" in name
                or "RRB CLERK" in name
            )

        # =====================================================
        # SSC
        # =====================================================

        elif category_upper == "SSC":

            matched = (
                "SSC" in subject_name
                or "SSC" in name
                or "SSC CGL" in name
                or "SSC CHSL" in name
                or "SSC JE" in name
                or "SSC MTS" in name
                or "SSC GD" in name
                or "SSC CPO" in name
                or "SSC STENOGRAPHER" in name
            
            )

        # =====================================================
        # RRB / RAILWAY
        # =====================================================

        elif category_upper in ["RRB", "RAILWAY"]:

            matched = (
                "RRB" in subject_name
                or "RAILWAY" in subject_name
                or "RRB" in name
                or "RAILWAY" in name
                or "RRB JE" in name
                or "RRB ALP" in name
                or "RRB NTPC" in name
                or "RRB GROUP D" in name

            )

        # =====================================================
        # OLYMIADS
        # =====================================================

        elif category_upper == "OTHERS":

            matched = not any(
                x in name
                for x in [
                    "10TH CLASS",
                    "9TH CLASS",
                    "8TH CLASS",
                    "7TH CLASS",
                    "6TH CLASS",
                    "5TH CLASS",
                    "4TH CLASS",
                    "3RD CLASS",
                    "2ND CLASS",
                    "1ST CLASS",     
                ]
            )

        if matched:
            category_results.append(result)

    # =========================================================
    # SUMMARY
    # =========================================================

    total_tests = len(category_results)

    total_attempted = sum(
        max(
            (r.total_questions or 0)
            - (r.unanswered or 0),
            0
        )
        for r in category_results
    )

    total_correct = sum(
        r.correct or 0
        for r in category_results
    )

    total_wrong = sum(
        r.wrong or 0
        for r in category_results
    )

    total_unanswered = sum(
        r.unanswered or 0
        for r in category_results
    )

    total_questions = sum(
        r.total_questions or 0
        for r in category_results
    )

    scores = [
        float(r.score or 0)
        for r in category_results
    ]

    average_score = (
        sum(scores) / len(scores)
        if scores
        else 0
    )

    highest_score = (
        max(scores)
        if scores
        else 0
    )

    accuracy = (
        (total_correct / total_attempted) * 100
        if total_attempted > 0
        else 0
    )

    # =========================================================
    # CHART DATA
    # =========================================================

    attempt_labels = []
    attempted_values = []
    unanswered_values = []
    accuracy_values = []
    score_values = []

    for result in category_results:

        test_name = result.mock_test.name

        attempt_labels.append(test_name)

        attempted = max(
            (result.total_questions or 0)
            - (result.unanswered or 0),
            0
        )

        attempted_values.append(attempted)

        unanswered_values.append(
            result.unanswered or 0
        )

        if attempted > 0:

            test_accuracy = (
                (result.correct or 0)
                / attempted
            ) * 100

        else:

            test_accuracy = 0

        accuracy_values.append(
            round(test_accuracy, 2)
        )

        score_values.append(
            float(result.score or 0)
        )

    # =========================================================
    # MOCK TEST LIST
    # =========================================================

    mock_tests = MockTest.objects.filter(
        subject__name__icontains=category
    ).prefetch_related(
        "questions"
    )

    # =========================================================
    # CAT SPECIAL FILTER
    # =========================================================

    if category_upper == "CAT":

        full_tests = []
        session_tests = []

        for mock_test in mock_tests:

            name = mock_test.name.upper()

            if "FULL MOCK TEST" in name:

                full_tests.append(mock_test)

            elif (
                "SESSION TEST" in name
            ):

                session_tests.append(mock_test)

        # Sort by test number/name
        full_tests.sort(
            key=lambda x: x.name
        )

        session_tests.sort(
            key=lambda x: x.name
        )

        ordered_mock_tests = (
            full_tests
            + session_tests
        )

    else:

        ordered_mock_tests = list(
            mock_tests
        )

    # =========================================================
    # TEST HISTORY
    #
    # ONLY ATTEMPTED TESTS ARE SHOWN
    # =========================================================

    test_data = []

    for mock_test in ordered_mock_tests:

        result = TestResult.objects.filter(
            user=request.user,
            mock_test=mock_test
        ).order_by(
            "-created_at"
        ).first()

        # ---------------------------------------------
        # Only show Test History for attempted tests
        # ---------------------------------------------

        if not result:
            continue

        total_q = mock_test.questions.count()

        attempted = max(
            (result.total_questions or total_q)
            - (result.unanswered or 0),
            0
        )

        accuracy_test = (
            (result.correct or 0)
            / attempted
            * 100
            if attempted > 0
            else 0
        )

        test_data.append({

            "mock_test": mock_test,

            "test_id": mock_test.id,

            "result_id": result.id,

            "attempted": attempted,

            "score": result.score or 0,

            "total_questions":
                result.total_questions or total_q,

            "correct":
                result.correct or 0,

            "wrong":
                result.wrong or 0,

            "unanswered":
                result.unanswered or 0,

            "attempts": 1,

            "accuracy":
                round(
                    accuracy_test,
                    2
                ),

        })

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {

        "category": category,

        "total_tests":
            total_tests,

        "total_mock_tests":
            len(ordered_mock_tests),

        "average_score":
            round(
                average_score,
                2
            ),

        "highest_score":
            round(
                highest_score,
                2
            ),

        "accuracy":
            round(
                accuracy,
                2
            ),

        "total_attempted":
            total_attempted,

        "total_correct":
            total_correct,

        "total_wrong":
            total_wrong,

        "total_unanswered":
            total_unanswered,

        "test_data":
            test_data,

        "attempt_labels":
            attempt_labels,

        "attempted_values":
            attempted_values,

        "unanswered_values":
            unanswered_values,

        "accuracy_values":
            accuracy_values,

        "score_values":
            score_values,

    }

    return render(
        request,
        "category_performance.html",
        context
    )

@login_required
def test_ranking(request, mock_test_id):

    mock_test = get_object_or_404(
        MockTest,
        id=mock_test_id
    )

    # ---------------------------------
    # ALL RESULTS FOR THIS TEST
    # ---------------------------------

    results = TestResult.objects.filter(
        mock_test=mock_test
    ).select_related(
        "user"
    ).order_by(
        "-score",
        "created_at"
    )

    # ---------------------------------
    # BEST SCORE OF EACH CANDIDATE
    # ---------------------------------

    candidate_results = {}

    for result in results:

        user_id = result.user_id

        # If candidate has attempted the test
        # more than once, keep the highest score.
        if user_id not in candidate_results:

            candidate_results[user_id] = result

        else:

            existing = candidate_results[user_id]

            if (
                result.score or 0
            ) > (
                existing.score or 0
            ):

                candidate_results[user_id] = result

    # ---------------------------------
    # SORT CANDIDATES BY SCORE
    # ---------------------------------

    ranking_results = sorted(
        candidate_results.values(),
        key=lambda r: (
            -(r.score or 0),
            r.created_at
        )
    )

    # ---------------------------------
    # CREATE RANKING
    # ---------------------------------

    ranking = []

    current_rank = 0
    previous_score = None

    for position, result in enumerate(
        ranking_results,
        start=1
    ):

        score = result.score or 0

        # Same score = same rank
        if score != previous_score:

            current_rank = position

        ranking.append({

            "rank": current_rank,

            "username":
                result.user.username,

            "score":
                score,

            "correct":
                result.correct or 0,

            "wrong":
                result.wrong or 0,

            "unanswered":
                result.unanswered or 0,

            "accuracy":
                round(
                    result.accuracy or 0,
                    2
                ),

            "result_id":
                result.id,

            "is_current_user":
                result.user_id == request.user.id,
        })

        previous_score = score

    # ---------------------------------
    # CURRENT USER
    # ---------------------------------

    current_candidate = None

    for candidate in ranking:

        if candidate["is_current_user"]:

            current_candidate = candidate
            break

    total_candidates = len(
        ranking
    )

    # ---------------------------------
    # PERCENTILE
    # ---------------------------------

    if (
        current_candidate
        and total_candidates > 1
    ):

        rank = current_candidate["rank"]

        percentile = (
            (
                total_candidates
                - rank
            )
            /
            total_candidates
        ) * 100

    elif current_candidate:

        percentile = 100

    else:

        percentile = 0

    # ---------------------------------
    # CONTEXT
    # ---------------------------------

    context = {

        "mock_test":
            mock_test,

        "ranking":
            ranking,

        "current_candidate":
            current_candidate,

        "total_candidates":
            total_candidates,

        "percentile":
            round(
                percentile,
                2
            ),
    }

    return render(
        request,
        "test_ranking.html",
        context
    )

@login_required
def test_result_detail(request, result_id):

    result = get_object_or_404(
        TestResult.objects.select_related(
            "mock_test",
            "mock_test__subject"
        ),
        id=result_id,
        user=request.user
    )

    answers = UserAnswer.objects.filter(
        test_result=result
    ).select_related(
        "question"
    ).order_by(
        "question__question_no",
        "question__id"
    )

    attempted = (
        int(result.correct or 0)
        + int(result.wrong or 0)
    )

    return render(
        request,
        "test_result_detail.html",
        {
            "result": result,
            "answers": answers,
            "attempted": attempted,
        }
    )

@login_required
def olympiad(request):
    return render(
        request,
        "olympiad.html",
        {
            "olympiad_classes": list(range(10, 0, -1)),
        }
    )


@login_required
def olympiad_class(request, class_no):
    if class_no < 1 or class_no > 10:
        raise Http404("Class not found")

    if class_no == 1:
        subjects = [
            {"slug": "mathematics", "name": "International Mathematics Olympiad"},
            {"slug": "science-gk", "name": "Science and GK Olympiad"},
            {"slug": "english", "name": "International English Olympiad"},
            {"slug": "logical-reasoning", "name": "Logical Reasoning Olympiad"},
        ]
    else:
        subjects = [
            {"slug": "mathematics", "name": "International Mathematics Olympiad"},
            {"slug": "science", "name": "National Science Olympiad"},
            {"slug": "english", "name": "International English Olympiad"},
            {"slug": "gk", "name": "International GK Olympiad"},
        ]

        if class_no == 10:
            subjects.append({
                "slug": "advanced-maths",
                "name": "Advanced Maths Olympiad",
            })

    return render(
        request,
        "olympiad_subjects.html",
        {"class_no": class_no, "subjects": subjects},
    )



def get_olympiad_mock_test(class_no, subject_slug, test_no):
    subject = get_object_or_404(Subject, id=13)

    subject_labels = {
        "mathematics": "Mathematics",
        "science": "Science",
        "english": "English",
        "gk": "GK",
        "advanced-maths": "Advanced Maths",
        "science-gk": "Science and GK",
        "logical-reasoning": "Logical Reasoning",
    }

    if subject_slug not in subject_labels:
        raise Http404("Olympiad category not found")

    # Use this exact naming convention in the database:
    # Class 9 Mathematics Test 1
    expected_name = (
        f"Class {class_no} "
        f"{subject_labels[subject_slug]} "
        f"Test {test_no}"
    )

    return MockTest.objects.filter(
        subject=subject,
        name__iexact=expected_name,
    ).first()


@login_required
def olympiad_subject(request, class_no, subject_slug):
    if not 1 <= class_no <= 10:
        raise Http404("Class not found")

    if class_no == 1:
        allowed = {
            "mathematics", "science-gk",
            "english", "logical-reasoning",
        }
    elif class_no == 10:
        allowed = {
            "mathematics", "science", "english",
            "gk", "advanced-maths",
        }
    else:
        allowed = {"mathematics", "science", "english", "gk"}

    if subject_slug not in allowed:
        raise Http404("Subject not available for this class")

    subject_labels = {
        "mathematics": "International Mathematics Olympiad",
        "science": "National Science Olympiad",
        "english": "International English Olympiad",
        "gk": "International GK Olympiad",
        "advanced-maths": "Advanced Maths Olympiad",
        "science-gk": "Science and GK Olympiad",
        "logical-reasoning": "Logical Reasoning Olympiad",
    }

    olympiad_tests = []

    for test_no in range(1, 11):
        mock_test = get_olympiad_mock_test(
            class_no, subject_slug, test_no
        )

        has_questions = (
            mock_test is not None
            and mock_test.questions.exists()
        )

        olympiad_tests.append({
            "test_no": test_no,
            "has_questions": has_questions,
        })

    return render(
        request,
        "olympiad_subject.html",
        {
            "class_no": class_no,
            "subject_slug": subject_slug,
            "subject_name": subject_labels[subject_slug],
            "olympiad_tests": olympiad_tests,
        },
    )


@login_required
def olympiad_test(request, class_no, subject_slug, test_no):
    if not 1 <= class_no <= 10 or not 1 <= test_no <= 10:
        raise Http404("Class or test not found")

    mock_test = get_olympiad_mock_test(
        class_no, subject_slug, test_no
    )

    if mock_test is None or not mock_test.questions.exists():
        return redirect(
            "olympiad_subject",
            class_no=class_no,
            subject_slug=subject_slug,
        )

    # Open the existing EduMind mock-test engine.
    return redirect("test", test_id=mock_test.id)


def get_olympiad_mock_test(class_no, subject_slug, test_no):

    subject = get_object_or_404(Subject, id=13)

    subject_labels = {
        "mathematics": "Mathematics",
        "science": "Science",
        "english": "English",
        "gk": "GK",
        "advanced-maths": "Advanced Maths",
        "science-gk": "Science and GK",
        "logical-reasoning": "Logical Reasoning",
    }

    if subject_slug not in subject_labels:
        raise Http404("Olympiad category not found")

    label = subject_labels[subject_slug]

    # Support the actual Class 10 Mathematics test name.
    if subject_slug == "mathematics":
        expected_name = (
            f"Class {class_no} International Mathematics Test - {test_no}"
        )

        mock_test = MockTest.objects.filter(
            subject=subject,
            name__iexact=expected_name,
        ).first()

        if mock_test:
            return mock_test

    # Support other common test naming formats.
    possible_names = [
        f"Class {class_no} {label} Test {test_no}",
        f"Class {class_no} {label} Test - {test_no}",
        f"Class {class_no} {label} Mock Test {test_no}",
    ]

    return MockTest.objects.filter(
        subject=subject,
        name__in=possible_names,
    ).first()


from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404, redirect, render

def verify_password_otp(request, otp_id):
    otp_record = get_object_or_404(
        EmailOTP,
        id=otp_id,
        user=request.user,
        is_used=False
    )

    if request.method == "POST":
        if timezone.now() >= (
            otp_record.created_at + timedelta(minutes=1)
        ):
            otp_record.is_used = True
            otp_record.save(update_fields=["is_used"])
            return render(request, "accounts/otp_expired.html")

        if otp_record.attempts >= 3:
            otp_record.is_used = True
            otp_record.save(update_fields=["is_used"])
            return render(request, "accounts/otp_locked.html")

        otp_record.attempts += 1
        otp_record.save(update_fields=["attempts"])

        entered_otp = request.POST.get("otp", "").strip()

        if check_password(entered_otp, otp_record.otp_hash):
            otp_record.is_used = True
            otp_record.save(update_fields=["is_used"])

            # Mark the email as verified here.
            return redirect("dashboard")

        if otp_record.attempts >= 3:
            otp_record.is_used = True
            otp_record.save(update_fields=["is_used"])
            return render(request, "accounts/otp_locked.html")

        return render(request, "accounts/verify_password_otp.html", {
            "error": "Incorrect OTP. Attempts remaining: "
                     f"{3 - otp_record.attempts}"
        })

    return render(request, "accounts/verify_password_otp.html")

import re
import secrets
import requests

from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from .models import PendingRegistration, PasswordResetOTP, Profile

User = get_user_model()

OTP_SECONDS = 60
OTP_MAX_ATTEMPTS = 3


def generate_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def normalize_mobile(value):
    """Accept a 10-digit Indian number or one prefixed by 91/+91."""
    value = re.sub(r"[\s()-]", "", value or "")

    if value.startswith("+91"):
        value = value[3:]
    elif value.startswith("91") and len(value) == 12:
        value = value[2:]

    if not re.fullmatch(r"[6-9]\d{9}", value):
        raise ValueError(
            "Enter a valid 10-digit Indian mobile number."
        )

    return value


def send_email_otp(email, otp, purpose):
    subject = f"EduMind {purpose} OTP"
    message = (
        f"Your EduMind OTP is {otp}.\n"
        f"It expires in {OTP_SECONDS} seconds.\n"
        "Do not share this code with anyone."
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_sms_otp(mobile, otp):
    """
    Send the generated OTP through MSG91 Flow API.
    The MSG91 template must use the configured variable.
    """
    authkey = getattr(settings, "MSG91_AUTHKEY", "")
    template_id = getattr(
        settings, "MSG91_FLOW_TEMPLATE_ID", ""
    )
    api_url = getattr(
        settings,
        "MSG91_FLOW_API_URL",
        "https://control.msg91.com/api/v5/flow/",
    )
    variable_name = getattr(
        settings, "MSG91_OTP_VARIABLE_NAME", "OTP"
    )

    if not authkey or not template_id:
        raise RuntimeError(
            "SMS provider is not configured. "
            "Set MSG91_AUTHKEY and MSG91_FLOW_TEMPLATE_ID."
        )

    payload = {
        "template_id": template_id,
        "recipients": [
            {
                "mobiles": "91" + mobile,
                variable_name: otp,
            }
        ],
    }

    response = requests.post(
        api_url,
        headers={
            "authkey": authkey,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=10,
    )
    response.raise_for_status()

    result = response.json()
    if str(result.get("type", "")).lower() == "error":
        raise RuntimeError("SMS provider rejected the request.")


def send_otp_pair(pending):
    email_otp = generate_otp()
    mobile_otp = generate_otp()
    now = timezone.now()

    # Save hashes, never the plaintext OTPs.
    pending.email_otp_hash = make_password(email_otp)
    pending.mobile_otp_hash = make_password(mobile_otp)
    pending.email_expires_at = now + timedelta(seconds=60)
    pending.mobile_expires_at = now + timedelta(seconds=60)
    pending.email_attempts = 0
    pending.mobile_attempts = 0
    pending.email_verified = False
    pending.mobile_verified = False
    pending.save()

    # Fail closed: registration cannot complete unless both
    # messages can be dispatched successfully.
    send_email_otp(
        pending.email, email_otp, "registration"
    )
    send_sms_otp(pending.mobile_number, mobile_otp)


def registration(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        raw_mobile = request.POST.get("mobile_number", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        try:
            mobile = normalize_mobile(raw_mobile)

            if not username or not email:
                raise ValueError(
                    "User ID and email are required."
                )

            if password != password2:
                raise ValueError("Passwords do not match.")

            if User.objects.filter(username=username).exists():
                raise ValueError("This user ID is already taken.")

            if User.objects.filter(email__iexact=email).exists():
                raise ValueError(
                    "This email address is already registered."
                )

            if Profile.objects.filter(
                mobile_number__in=[mobile, "+91" + mobile]
            ).exists():
                raise ValueError(
                    "This mobile number is already registered."
                )

            validate_password(password)

            # Remove stale registrations before creating a new one.
            PendingRegistration.objects.filter(
                created_at__lt=timezone.now() - timedelta(hours=1)
            ).delete()

            if PendingRegistration.objects.filter(
                username=username
            ).exists():
                raise ValueError(
                    "A registration for this user ID is pending."
                )

            pending = PendingRegistration.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                mobile_number=mobile,
                password_hash=make_password(password),
                email_otp_hash="",
                mobile_otp_hash="",
                email_expires_at=timezone.now(),
                mobile_expires_at=timezone.now(),
            )

            try:
                send_otp_pair(pending)
            except Exception:
                pending.delete()
                raise RuntimeError(
                    "OTP delivery failed. Check email/SMS settings "
                    "and try registering again."
                )

            request.session["pending_registration_id"] = str(
                pending.pk
            )
            return redirect("verify_registration")

        except (ValueError, ValidationError, RuntimeError) as exc:
            return render(request, "accounts/register.html", {
                "error": str(exc),
                "form_data": request.POST,
            })

    return render(request, "accounts/register.html")


@require_http_methods(["GET", "POST"])
@csrf_protect
def verify_registration(request):
    pending_id = request.session.get(
        "pending_registration_id"
    )

    if not pending_id:
        messages.error(
            request,
            "Please begin registration first."
        )
        return redirect("register")

    pending = get_object_or_404(
        PendingRegistration,
        pk=pending_id,
    )

    if request.method == "POST":
        email_code = request.POST.get("email_otp", "").strip()
        mobile_code = request.POST.get("mobile_otp", "").strip()
        now = timezone.now()

        errors = []

        for channel, code in (
            ("email", email_code),
            ("mobile", mobile_code),
        ):
            verified_field = f"{channel}_verified"
            attempts_field = f"{channel}_attempts"
            hash_field = f"{channel}_otp_hash"
            expiry_field = f"{channel}_expires_at"

            if getattr(pending, verified_field):
                continue

            attempts = getattr(pending, attempts_field)
            expiry = getattr(pending, expiry_field)

            if attempts >= OTP_MAX_ATTEMPTS:
                errors.append(
                    f"{channel.title()} OTP has reached its "
                    "attempt limit. Restart registration."
                )
                continue

            if now >= expiry:
                errors.append(
                    f"{channel.title()} OTP expired. "
                    "Restart registration to receive new codes."
                )
                continue

            setattr(pending, attempts_field, attempts + 1)

            if (
                len(code) == 6
                and code.isdigit()
                and check_password(
                    code, getattr(pending, hash_field)
                )
            ):
                setattr(pending, verified_field, True)
            else:
                remaining = OTP_MAX_ATTEMPTS - (
                    attempts + 1
                )
                errors.append(
                    f"Incorrect {channel} OTP. "
                    f"Attempts remaining: {remaining}."
                )

        pending.save()

        if errors:
            return render(
                request,
                "accounts/verify_registration.html",
                {"errors": errors, "pending": pending},
            )

        if pending.email_verified and pending.mobile_verified:
            try:
                with transaction.atomic():
                    user = User.objects.create(
                        username=pending.username,
                        first_name=pending.first_name,
                        last_name=pending.last_name,
                        email=pending.email,
                        password=pending.password_hash,
                        is_active=True,
                    )

                    # If your post-save signal creates Profile,
                    # this retrieves it; otherwise it creates one.
                    profile, _ = Profile.objects.get_or_create(
                        user=user
                    )
                    profile.mobile_number = pending.mobile_number
                    profile.save()

                    pending.delete()

            except Exception:
                messages.error(
                    request,
                    "Registration could not be completed. "
                    "Please contact support."
                )
                return redirect("register")

            request.session.pop(
                "pending_registration_id", None
            )
            messages.success(
                request,
                "Registration complete. Please log in."
            )
            return redirect("login")

    return render(
        request,
        "accounts/verify_registration.html",
        {"pending": pending},
    )


@require_http_methods(["POST"])
def resend_registration_otp(request):
    pending_id = request.session.get(
        "pending_registration_id"
    )
    if not pending_id:
        return redirect("register")

    pending = get_object_or_404(
        PendingRegistration, pk=pending_id
    )

    try:
        send_otp_pair(pending)
    except Exception:
        messages.error(
            request,
            "Could not send new OTPs. Please try again later."
        )
        return redirect("verify_registration")

    messages.success(
        request,
        "New OTPs sent. Previous OTPs are invalid."
    )
    return redirect("verify_registration")

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import PasswordResetOTP, Profile


def forgot_password(request):
    User = get_user_model()

    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()

        user = User.objects.filter(
            email__iexact=identifier
        ).first()

        channel = "email"

        if not user:
            try:
                mobile = normalize_mobile(identifier)
            except ValueError:
                mobile = None

            if mobile:
                profile = Profile.objects.filter(
                    Q(mobile_number=mobile) |
                    Q(mobile_number="+91" + mobile)
                ).select_related("user").first()

                if profile:
                    user = profile.user
                    channel = "mobile"

        if not user:
            return render(request, "forgot_password.html", {
                "error": "No account was found for those details."
            })

        otp = generate_otp()
        now = timezone.now()

        PasswordResetOTP.objects.filter(
            user=user,
            channel=channel,
            is_used=False
        ).update(is_used=True)

        record = PasswordResetOTP.objects.create(
            user=user,
            channel=channel,
            code_hash=make_password(otp),
            expires_at=now + timedelta(seconds=OTP_SECONDS),
        )

        try:
            if channel == "email":
                send_email_otp(user.email, otp, "password reset")
            else:
                send_sms_otp(mobile, otp)
        except Exception:
            record.is_used = True
            record.save(update_fields=["is_used"])
            return render(request, "forgot_password.html", {
                "error": "OTP delivery failed. Check the email/SMS settings and try again."
            })

        request.session["password_reset_otp_id"] = str(record.pk)
        return redirect("verify_password_reset_otp")

    return render(request, "forgot_password.html")


def verify_password_reset_otp(request):
    otp_id = request.session.get("password_reset_otp_id")

    if not otp_id:
        return redirect("forgot_password")

    record = PasswordResetOTP.objects.filter(
        pk=otp_id,
        is_used=False
    ).first()

    if not record:
        request.session.pop("password_reset_otp_id", None)
        return redirect("forgot_password")

    if request.method == "POST":
        now = timezone.now()

        if record.verified_at:
            return redirect("set_new_password")

        if now >= record.expires_at:
            record.is_used = True
            record.save(update_fields=["is_used"])
            return render(request, "accounts/verify_password_otp.html", {
                "error": "OTP expired. Please request a new one."
            })

        if record.attempts >= OTP_MAX_ATTEMPTS:
            record.is_used = True
            record.save(update_fields=["is_used"])
            return render(request, "accounts/verify_password_otp.html", {
                "error": "Too many incorrect attempts. Request a new OTP."
            })

        entered_otp = request.POST.get("otp", "").strip()
        record.attempts += 1

        if (
            len(entered_otp) == 6
            and entered_otp.isdigit()
            and check_password(entered_otp, record.code_hash)
        ):
            record.verified_at = now
            record.save(update_fields=["attempts", "verified_at"])
            return redirect("set_new_password")

        if record.attempts >= OTP_MAX_ATTEMPTS:
            record.is_used = True
            record.save(update_fields=["attempts", "is_used"])
            error = "Too many incorrect attempts. Request a new OTP."
        else:
            error = (
                "Incorrect OTP. Attempts remaining: "
                f"{OTP_MAX_ATTEMPTS - record.attempts}."
            )

        record.save(update_fields=["attempts", "is_used"])
        return render(request, "accounts/verify_password_otp.html", {
            "error": error
        })

    return render(request, "accounts/verify_password_otp.html")


def set_new_password(request):
    otp_id = request.session.get("password_reset_otp_id")

    if not otp_id:
        return redirect("forgot_password")

    record = PasswordResetOTP.objects.filter(
        pk=otp_id,
        is_used=False,
        verified_at__isnull=False,
    ).first()

    if not record:
        return redirect("forgot_password")

    if timezone.now() >= record.expires_at:
        record.is_used = True
        record.save(update_fields=["is_used"])
        request.session.pop("password_reset_otp_id", None)
        return redirect("forgot_password")

    if request.method == "POST":
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        if password != password2:
            return render(request, "accounts/set_new_password.html", {
                "error": "Passwords do not match."
            })

        try:
            validate_password(password, user=record.user)
        except ValidationError as exc:
            return render(request, "accounts/set_new_password.html", {
                "error": " ".join(exc.messages)
            })

        record.user.set_password(password)
        record.user.save(update_fields=["password"])

        record.is_used = True
        record.save(update_fields=["is_used"])

        PasswordResetOTP.objects.filter(
            user=record.user,
            is_used=False
        ).update(is_used=True)

        request.session.pop("password_reset_otp_id", None)
        messages.success(request, "Password changed. Please log in.")
        return redirect("login")

    return render(request, "accounts/set_new_password.html")