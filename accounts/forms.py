# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        # UserCreationForm provides password1 & password2 automatically
        fields = ("username", "email", "first_name", "last_name")
        widgets = {"email": forms.EmailInput(attrs={"autocomplete": "email"})}


