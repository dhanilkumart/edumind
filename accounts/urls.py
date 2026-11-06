from django.urls import path
from . import views


urlpatterns = [

    # =================================================
    # HOME
    # =================================================

    path("", views.home, name="home"),
    path("home/", views.home, name="home_page"),

    # =================================================
    # AUTHENTICATION AND OTP VERIFICATION
    # =================================================
    
    path("register/", views.register, name="register"),

    path(
        "verify-registration/",
        views.verify_registration,
        name="verify_registration",
    ),

    path(
        "resend-registration-otp/",
        views.resend_registration_otp,
        name="resend_registration_otp",
    ),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path(
        "forgot-password/",
        views.forgot_password,
        name="forgot_password",
    ),

path(
    "verify-password-otp/",
    views.verify_password_reset_otp,
    name="verify_password_otp",
),

    path(
        "set-new-password/",
        views.set_new_password,
        name="set_new_password",
    ),

    # =================================================
    # DASHBOARD
    # =================================================

    path("dashboard/", views.dashboard, name="dashboard"),

    # =================================================
    # MAIN PAGES
    # =================================================

    path("exams/", views.exams, name="exams"),
    path("subjects/", views.subjects, name="subjects"),
    path("mock_tests/", views.mock_tests, name="mock_tests"),
    path("previous_tests/", views.previous_tests, name="previous_tests"),

    path(
        "performance/",
        views.performance,
        name="performance_analysis",
    ),

    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings_view, name="settings"),

    # =================================================
    # QUESTION UPLOAD
    # =================================================

    path(
        "upload_questions/",
        views.upload_questions,
        name="upload_questions",
    ),

    # =================================================
    # SUBJECT MOCK TESTS
    # =================================================

    path(
        "subject/<int:subject_id>/mock_tests/",
        views.subject_mock_tests,
        name="subject_mock_tests",
    ),

    # =================================================
    # CAT
    # =================================================

    path("cat/", views.cat, name="cat"),

    path(
        "cat/full-mock-tests/",
        views.cat_full_mock_tests,
        name="cat_full_mock_tests",
    ),

    path(
        "cat/session-tests/",
        views.cat_session_tests,
        name="cat_session_tests",
    ),

    # =================================================
    # MOCK TEST, REVIEW AND SUBMISSION
    # =================================================

    path(
        "test/<int:test_id>/",
        views.test_view,
        name="test",
    ),

    path(
        "review/<int:test_id>/",
        views.review_test,
        name="review_test",
    ),

    path(
        "review/<int:test_id>/<int:question_no>/",
        views.review_test,
        name="review_question",
    ),

    path(
        "result/<int:test_id>/",
        views.result_detail,
        name="result_detail",
    ),

    path(
        "submit-test/<int:mock_test_id>/",
        views.submit_test,
        name="submit_test",
    ),

    # =================================================
    # BANKING
    # =================================================

    path("banking/", views.banking, name="banking"),

    path(
        "banking/sbi-po/",
        views.bank_exam_tests,
        {"exam_key": "sbi-po"},
        name="sbi_po",
    ),

    path(
        "banking/sbi-clerk/",
        views.bank_exam_tests,
        {"exam_key": "sbi-clerk"},
        name="sbi_clerk",
    ),

    path(
        "banking/ibps-po/",
        views.bank_exam_tests,
        {"exam_key": "ibps-po"},
        name="ibps_po",
    ),

    path(
        "banking/ibps-clerk/",
        views.bank_exam_tests,
        {"exam_key": "ibps-clerk"},
        name="ibps_clerk",
    ),

    path(
        "banking/rrb-po/",
        views.bank_exam_tests,
        {"exam_key": "rrb-po"},
        name="rrb_po",
    ),

    path(
        "banking/rrb-office-assistant/",
        views.bank_exam_tests,
        {"exam_key": "rrb-office-assistant"},
        name="rrb_office_assistant",
    ),

    path(
        "banking/rbi-grade-b/",
        views.bank_exam_tests,
        {"exam_key": "rbi-grade-b"},
        name="rbi_grade_b",
    ),

    path(
        "banking/rbi-assistant/",
        views.bank_exam_tests,
        {"exam_key": "rbi-assistant"},
        name="rbi_assistant",
    ),

    # =================================================
    # SSC EXAMS
    # =================================================

    path("ssc/", views.ssc, name="ssc"),
    path("ssc/cgl/", views.ssc_cgl, name="ssc_cgl"),
    path("ssc/chsl/", views.ssc_chsl, name="ssc_chsl"),
    path("ssc/je/", views.ssc_je, name="ssc_je"),
    path("ssc/mts/", views.ssc_mts, name="ssc_mts"),
    path("ssc/gd/", views.ssc_gd, name="ssc_gd"),
    path("ssc/cpo/", views.ssc_cpo, name="ssc_cpo"),

    path(
        "ssc/stenographer/",
        views.ssc_stenographer,
        name="ssc_stenographer",
    ),

    # =================================================
    # RAILWAY / RRB EXAMS
    # =================================================

    path("railway/", views.railway, name="railway"),

    path(
        "rrb-je/",
        views.rrb_je_cbt1_mock_tests,
        name="rrb_je",
    ),

    path(
        "rrb-je/cbt-1/",
        views.rrb_je_cbt1_mock_tests,
        name="rrb_je_cbt1_mock_tests",
    ),

    path(
        "railway/rrb-alp/",
        views.rrb_alp,
        name="rrb_alp",
    ),

    path(
        "railway/rrb-ntpc/",
        views.rrb_ntpc,
        name="rrb_ntpc",
    ),

    path(
        "railway/rrb-group-d/",
        views.rrb_group_d,
        name="rrb_group_d",
    ),

    # =================================================
    # OTHER EXAM CATEGORIES
    # =================================================

    path("10th-pass/", views.tenth_pass, name="tenth_pass"),
    path("12th-pass/", views.twelfth_pass, name="twelfth_pass"),
    path("graduate/", views.graduate, name="graduate"),
    path("engineering/", views.engineering, name="engineering"),
    path("specialized/", views.specialized, name="specialized"),
    path("olympiad/", views.olympiad, name="olympiad"),

    # =================================================
    # OLYMPIAD CLASS AND SUBJECT PAGES
    # =================================================

    path(
        "olympiad/class/<int:class_no>/",
        views.olympiad_class,
        name="olympiad_class",
    ),

    path(
        "olympiad/class/<int:class_no>/<slug:subject_slug>/",
        views.olympiad_subject,
        name="olympiad_subject",
    ),

    path(
        "olympiad/class/<int:class_no>/<slug:subject_slug>/test/<int:test_no>/",
        views.olympiad_test,
        name="olympiad_test",
    ),

    # =================================================
    # PERFORMANCE AND RANKING
    # =================================================

    path(
        "performance/category/<str:category>/",
        views.category_performance,
        name="category_performance",
    ),

    path(
        "performance/ranking/<int:mock_test_id>/",
        views.test_ranking,
        name="test_ranking",
    ),

    path(
        "performance/test-result/<int:result_id>/",
        views.test_result_detail,
        name="test_result_detail",
    ),

    path(
    "verify-password-reset-otp/",
    views.verify_password_reset_otp,
    name="verify_password_reset_otp",
),

]

