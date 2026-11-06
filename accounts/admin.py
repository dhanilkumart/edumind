from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import (
    Question,
    Subject,
    UserAnswer,
    TestResult,
    Profile,
    MockTest,
    TestSection,
)


class TestSectionInline(admin.TabularInline):
    model = TestSection
    extra = 1


@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "subject",
        "duration_minutes",
        "timing_mode",
    )

    list_filter = (
        "subject",
        "timing_mode",
    )

    search_fields = ("name",)

    inlines = [TestSectionInline]


admin.site.register(TestResult)
admin.site.register(Subject)
admin.site.register(Question)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Profile)
admin.site.register(UserAnswer)