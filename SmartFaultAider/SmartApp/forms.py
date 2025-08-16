# SmartApp/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Asset

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
    attachment = forms.FileField(
        label='Attach a file (optional)',
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    def clean_attachment(self):
        file = self.cleaned_data.get('attachment')
        if not file:
            return file
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'application/pdf'
        ]
        max_size = 5 * 1024 * 1024  # 5MB
        if file.content_type not in allowed_types:
            raise forms.ValidationError('Only JPG, PNG, GIF images and PDF files are allowed.')
        if file.size > max_size:
            raise forms.ValidationError('File size must be under 5MB.')
        return file

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = '__all__'
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_expiry': forms.DateInput(attrs={'type': 'date'}),
            'date_reported': forms.DateInput(attrs={'type': 'date'}),
        }
