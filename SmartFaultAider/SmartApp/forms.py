# SmartApp/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class ChatForm(forms.Form):
    question = forms.CharField(
        label='Ask a question',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Describe your issue...',
            'class': 'form-control'
        })
    )
