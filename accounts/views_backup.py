from operator import index

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
)

from .forms import ExcelUploadForm

import json
import random
from pathlib import Path

import openpyxl
@login_required
def exams(request):

    # Get all mock tests
    mock_tests = MockTest.objects.select_related(
        "subject"
    ).all().order_by("id")

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
        "subject_mock_tests.html",
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

def register(request):
    if request.method == "POST":

        username = request.POST["username"].strip()
        email = request.POST["email"].strip()

        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already exists.")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=request.POST["password"],
            first_name=request.POST["first_name"],
            last_name=request.POST["last_name"]
        )

        Profile.objects.get_or_create(
    user=user,
    defaults={
        "mobile_number": request.POST["mobile_number"]
    }
)
        return redirect("login")

    return render(request, "register.html")



    return render(
        request,
        "review.html",
        {
            "review_questions": review_questions,
        }
    )

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

def review_test(request, test_id, question_no=1):

    if not request.user.is_authenticated:
        return redirect("login")

    # Get the attempted test
    test = get_object_or_404(
        TestResult,
        id=test_id,
        user=request.user
    )

    # Get all answers belonging to this test
    answers = list(
        UserAnswer.objects
        .filter(test_result=test)
        .select_related("question")
        .order_by("question__question_no", "id")
    )

    total_questions = len(answers)

    # No answers saved
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

    # Keep question number within range
    question_no = max(1, min(question_no, total_questions))

    # Current answer
    answer = answers[question_no - 1]

    return render(
        request,
        "review_test.html",
        {
            "test": test,
            "answer": answer,
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

def subjects(request):
    if not request.user.is_authenticated:
        return redirect("login")

    all_subjects = Subject.objects.all()

    return render(
        request,
        "subjects.html",
        {
            "subjects": all_subjects,
        }
    )

@login_required
def subject_mock_tests(request, subject_id):

    subject = get_object_or_404(
        Subject,
        id=subject_id
    )

    mock_tests = MockTest.objects.filter(
        subject=subject
    )

    attempted_test_ids = set(
    TestResult.objects.filter(
        user=request.user,
        mock_test__isnull=False
    ).values_list(
        "mock_test_id",
        flat=True
    )
)

    for test in mock_tests:
        print("================================")
        print("Mock Test ID:", test.id)
        print("Mock Test Name:", test.name)
        print(
            "Question Count:",
            Question.objects.filter(mock_test=test).count()
        )
        print("================================")

    return render(
    request,
    "subject_mock_tests.html",
    {
        "subject": subject,
        "mock_tests": mock_tests,
        "attempted_test_ids": attempted_test_ids,
    }
)   


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

            # Read header row
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

            # Find columns
            question_col = headers.index("question")

            if "option a" in headers:

                option_a_col = headers.index("option a")
                option_b_col = headers.index("option b")
                option_c_col = headers.index("option c")
                option_d_col = headers.index("option d")

            elif "choice a" in headers:

                option_a_col = headers.index("choice a")
                option_b_col = headers.index("choice b")
                option_c_col = headers.index("choice c")
                option_d_col = headers.index("choice d")

            else:

                return HttpResponse(
                    "Excel file must contain Option A-D "
                    "or Choice A-D."
                )

            answer_col = headers.index(
                "correct answer"
            )

            if "explanation" in headers:

                explanation_col = headers.index(
                    "explanation"
                )

            else:

                explanation_col = None

            # Read questions
            for row in sheet.iter_rows(
                min_row=2,
                values_only=True
            ):

                row = list(row)

                # Make sure row is long enough
                while len(row) <= max(
                    question_col,
                    option_a_col,
                    option_b_col,
                    option_c_col,
                    option_d_col,
                    answer_col
                ):
                    row.append(None)

                question_text = row[question_col]

                if not question_text:
                    continue

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

                correct_answer = str(
                    row[answer_col] or ""
                ).strip()

                if explanation_col is not None:
                    explanation = str(
                        row[explanation_col] or ""
                    ).strip()
                else:
                    explanation = ""

                # Determine correct option
                if correct_answer.upper() in [
                    "A", "B", "C", "D"
                ]:

                    correct_option = (
                        correct_answer.upper()
                    )

                elif correct_answer.lower() == option_a.lower():

                    correct_option = "A"

                elif correct_answer.lower() == option_b.lower():

                    correct_option = "B"

                elif correct_answer.lower() == option_c.lower():

                    correct_option = "C"

                elif correct_answer.lower() == option_d.lower():

                    correct_option = "D"

                else:

                    continue

                Question.objects.create(
                    mock_test=mock_test,
                    question=str(
                        question_text
                    ).strip(),
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_option=correct_option,
                    explanation=explanation
                )

                uploaded_count += 1

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

def cat(request):
    return render(request, "cat.html")


def banking(request):
    return render(request, "banking.html")


from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Subject, MockTest


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

@login_required
def ssc_cgl(request):
    subject = get_object_or_404(
        Subject,
        name__iexact="SSC"
    )

    mock_tests = MockTest.objects.filter(
        subject=subject,
        name__regex=r"^Mock Test ([1-9]|10)$"
    ).order_by("id")

    mock_tests = sorted(
        mock_tests,
        key=lambda test: int(test.name.split()[-1])
    )

    return render(
        request,
        "exams/ssc/ssc_cgl.html",
        {"mock_tests": mock_tests}
    )


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


def olympiad(request):
    return render(request, "olympiad.html")

@login_required
def test_ranking(request, mock_test_id):

    mock_test = get_object_or_404(
        MockTest,
        id=mock_test_id
    )

    # All attempts for this specific mock test
    all_results = TestResult.objects.filter(
        mock_test=mock_test
    ).select_related(
        "user"
    )

    # Keep the best score of each candidate
    best_results = {}

    for result in all_results:

        user_id = result.user_id

        if user_id not in best_results:
            best_results[user_id] = result

        else:
            existing = best_results[user_id]

            if float(result.score or 0) > float(existing.score or 0):
                best_results[user_id] = result

    # Convert to list
    rankings = list(best_results.values())

    # Calculate rank and additional values
current_rank = 0
previous_score = None

for index, result in enumerate(rankings):

    score = float(result.score or 0)

    # Same score = same rank
    if score != previous_score:
        current_rank = index + 1
        previous_score = score

    result.rank = current_rank

    result.attempted = (
        int(result.correct or 0)
        + int(result.wrong or 0)
    )

    result.unattended = int(
        result.unanswered or 0
    )

    # Find the logged-in user's ranking
my_rank = None
my_result = None

for result in rankings:
    if result.user_id == request.user.id:
        my_rank = result.rank
        my_result = result
        break

    result.attempted = (
            int(result.correct or 0)
            + int(result.wrong or 0)
        )

    result.unattended = int(
            result.unanswered or 0
        )

    # Find the logged-in user's ranking
my_rank = None
my_result = None

for result in rankings:
    if result.user_id == request.user.id:
        my_rank = result.rank
        my_result = result
        break

    return render(
    request,
    "test_ranking.html",
    {
        "mock_test": mock_test,
        "rankings": rankings,
        "my_rank": my_rank,
        "my_result": my_result,
    }
)

@login_required
def category_performance(request, category):

    category_map = {
        "cat": "CAT",
        "bank": "BANK",
        "ssc": "SSC",
        "rrb": "RRB",
        "olympiad": "OLYMPIAD",
        "others": "OTHERS",
    }

    category_name = category_map.get(
        category.lower(),
        category.upper()
    )

    results = TestResult.objects.filter(
        user=request.user
    ).select_related(
        "mock_test"
    ).order_by("-created_at")

    category_results = []

    for result in results:

        if not result.mock_test:
            continue

        subject_name = ""

        if result.mock_test.subject:
            subject_name = result.mock_test.subject.name.upper()

        matched = False

        if category_name == "CAT":
            matched = subject_name == "CAT"

        elif category_name == "BANK":
            matched = subject_name in ["BANK", "BANKING"]

        elif category_name == "SSC":
            matched = subject_name == "SSC"

        elif category_name == "RRB":
            matched = subject_name in ["RRB", "RAILWAY"]

        elif category_name == "OLYMPIAD":
            matched = "OLYMPIAD" in subject_name

        elif category_name == "OTHERS":
            matched = subject_name not in [
                "CAT",
                "BANK",
                "BANKING",
                "SSC",
                "RRB",
                "RAILWAY"
            ] and "OLYMPIAD" not in subject_name

        if matched:
            result.attempted = (
                int(result.correct or 0)
                + int(result.wrong or 0)
            )

            category_results.append(result)

    total_tests = len(category_results)

    total_correct = sum(
        int(r.correct or 0)
        for r in category_results
    )

    total_wrong = sum(
        int(r.wrong or 0)
        for r in category_results
    )

    total_unanswered = sum(
        int(r.unanswered or 0)
        for r in category_results
    )

    total_score = sum(
        float(r.score or 0)
        for r in category_results
    )

    if total_tests > 0:
        average_score = round(
            total_score / total_tests,
            2
        )
    else:
        average_score = 0

    highest_score = max(
        [float(r.score or 0) for r in category_results],
        default=0
    )

    total_attempted = (
        total_correct + total_wrong
    )

    if total_attempted > 0:
        accuracy = round(
            (total_correct / total_attempted) * 100,
            2
        )
    else:
        accuracy = 0

    return render(
        request,
        "category_performance.html",
        {
            "category": category_name,
            "results": category_results,
            "total_tests": total_tests,
            "average_score": average_score,
            "highest_score": highest_score,
            "accuracy": accuracy,
            "total_correct": total_correct,
            "total_wrong": total_wrong,
            "total_unanswered": total_unanswered,
            "total_attempted": total_attempted,
        }
    )

@login_required
def test_ranking(request, mock_test_id):

    mock_test = get_object_or_404(
        MockTest,
        id=mock_test_id
    )

    results = TestResult.objects.filter(
        mock_test=mock_test
    ).select_related(
        "user"
    ).order_by(
        "-score",
        "time_taken",
        "created_at"
    )

    ranking = []

    for position, result in enumerate(results, start=1):

        attempted = (
            int(result.correct or 0)
            + int(result.wrong or 0)
        )

        ranking.append({
            "rank": position,
            "username": result.user.username,
            "score": result.score,
            "attempted": attempted,
            "correct": result.correct,
            "wrong": result.wrong,
            "unanswered": result.unanswered,
            "time_taken": result.time_taken,
        })

    return render(
        request,
        "test_ranking.html",
        {
            "mock_test": mock_test,
            "ranking": ranking,
        }
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