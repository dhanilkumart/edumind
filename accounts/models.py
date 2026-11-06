from django.db import models

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name



class MockTest(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)

    duration_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Time allowed for this mock test in minutes."
    )

    timing_mode = models.CharField(
    max_length=20,
    choices=[
        ("OVERALL", "Overall Timer"),
        ("SECTIONAL", "Sectional Timer"),
    ],
    default="OVERALL"
)

    def __str__(self):
        return f"{self.subject.name} - {self.name}"


class Question(models.Model):
    mock_test = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name="questions",
        null=True,
        blank=True
    )

    question_no = models.PositiveIntegerField(default=1)

    question = models.TextField(blank=True, default="")
    option_a = models.CharField(max_length=200, default="")
    option_b = models.CharField(max_length=200, default="")
    option_c = models.CharField(max_length=200, default="")
    option_d = models.CharField(max_length=200, default="")
    correct_option = models.CharField(max_length=1, default="A")
    explanation = models.TextField(blank=True, null=True, default="")

    section = models.ForeignKey(
        "TestSection",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions"
    )

    def __str__(self):
        return self.question

    
from django.contrib.auth.models import User

from django.db import models
from django.contrib.auth.models import User


class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    mock_test = models.ForeignKey(
        'MockTest',
        on_delete=models.CASCADE,
        related_name='results',
        null=True,
        blank=True
    )

    test_name = models.CharField(max_length=200, default="Mock Test")

    total_questions = models.IntegerField(default=0)
    correct = models.IntegerField(default=0)
    wrong = models.IntegerField(default=0)
    unanswered = models.IntegerField(default=0)

    score = models.FloatField(default=0)
    accuracy = models.FloatField(default=0)

    time_taken = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.test_name}"

class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    mobile_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.user.username


class UserAnswer(models.Model):
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField()
    time_spent = models.IntegerField(default=0)  # seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.question} - {self.selected_option}"

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):

    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):

    Profile.objects.get_or_create(user=instance)
    instance.profile.save()


from django.db import models
from django.contrib.auth.models import User

class TestAttempt(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    mock_test = models.ForeignKey(
        "MockTest",
        on_delete=models.CASCADE
    )

    score = models.FloatField(default=0)

    total_questions = models.PositiveIntegerField(default=0)

    attempted_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-attempted_at"]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.mock_test.name} - "
            f"{self.score}"
        )


class MobileOTP(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mobile_otps"
    )

    otp = models.CharField(max_length=6)

    created_at = models.DateTimeField(auto_now_add=True)

    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.otp}"


import uuid

from django.db import models
from django.utils import timezone


class PendingRegistration(models.Model):
    """
    Registration data is stored temporarily.
    A User account is created only after both OTPs are verified.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=20)
    password_hash = models.CharField(max_length=128)

    email_otp_hash = models.CharField(max_length=128)
    mobile_otp_hash = models.CharField(max_length=128)

    created_at = models.DateTimeField(auto_now_add=True)
    email_expires_at = models.DateTimeField()
    mobile_expires_at = models.DateTimeField()

    email_attempts = models.PositiveSmallIntegerField(default=0)
    mobile_attempts = models.PositiveSmallIntegerField(default=0)

    email_verified = models.BooleanField(default=False)
    mobile_verified = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["mobile_number"]),
        ]


class PasswordResetOTP(models.Model):
    """
    One OTP challenge for a registered user's selected
    email address or mobile number.
    """
    CHANNELS = [
        ("email", "Email"),
        ("mobile", "Mobile"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
    )
    channel = models.CharField(max_length=10, choices=CHANNELS)
    code_hash = models.CharField(max_length=128)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)

    is_used = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

import time
from django.db import models
from django.conf import settings

class EmailOTP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    otp_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)


import uuid

from django.db import models
from django.utils import timezone


class TestSection(models.Model):

    mock_test = models.ForeignKey(
        MockTest,
        on_delete=models.CASCADE,
        related_name="sections"
    )

    name = models.CharField(max_length=100)

    duration_minutes = models.PositiveIntegerField(
        default=30
    )

    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.mock_test.name} - {self.name}"