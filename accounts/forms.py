from django import forms
from django.contrib.auth.models import User
from .models import MockTest


class ExcelUploadForm(forms.Form):
    mock_test = forms.ModelChoiceField(
        queryset=MockTest.objects.all(),
        label="Select Mock Test"
    )

    excel_file = forms.FileField(
        label="Select Excel File"
    )


class RegistrationForm(forms.ModelForm):
    mobile_number = forms.CharField(
        max_length=15,
        required=True,
        label="Mobile Number",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter mobile number",
                "inputmode": "numeric"
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter password"
            }
        ),
        label="Password"
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm password"
            }
        ),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ["username"]

    def clean_mobile_number(self):
        mobile = self.cleaned_data["mobile_number"].strip()

        if not mobile.isdigit():
            raise forms.ValidationError(
                "Please enter a valid mobile number."
            )