from django import forms
from django.contrib.auth.forms import AuthenticationForm, \
    UserCreationForm, UserChangeForm
from .models import User
from django.core.exceptions import ValidationError



class UserLoginForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField()
    
    
    class Meta:
        model = User
        fields = ['username', 'password']
        

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    username = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2',
        )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is not free")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is not free")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords are not similar")
        
        return cleaned_data
        

class ProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            'image',
            'first_name',
            'last_name',
            'username',
            'email',
        )
    
    
        image = forms.ImageField(required=False)
        first_name = forms.CharField()
        last_name = forms.CharField()
        username = forms.CharField()
        email = forms.CharField()