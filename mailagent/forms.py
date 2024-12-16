from django import forms
from django.contrib.auth.forms import PasswordResetForm
from main.models import User

class CustomPasswordResetForm(PasswordResetForm):
    class Meta:
        model = User
        fields = ['email']