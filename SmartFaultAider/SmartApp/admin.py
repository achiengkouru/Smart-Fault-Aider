# SmartApp/admin.py

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.shortcuts import render

# Form to reset password
class PasswordResetForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.HiddenInput)
    new_password = forms.CharField(label="New Password", widget=forms.PasswordInput)


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'reset_password_link')
    search_fields = ('username', 'email')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reset-password/<int:user_id>/', self.admin_site.admin_view(self.reset_password_view), name='reset_user_password'),
        ]
        return custom_urls + urls

    def reset_password_link(self, obj):
        return format_html(
            '<a class="button" href="{}">Reset Password</a>',
            f"/admin/auth/user/reset-password/{obj.pk}/"
        )
    reset_password_link.short_description = 'Reset Password'
    reset_password_link.allow_tags = True

    def reset_password_view(self, request, user_id):
        user = User.objects.get(pk=user_id)

        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                new_password = form.cleaned_data['new_password']
                user.password = make_password(new_password)
                user.save()
                self.message_user(request, f"Password reset for user '{user.username}'", messages.SUCCESS)
                return redirect(f'/admin/auth/user/')
        else:
            form = PasswordResetForm(initial={'_selected_action': user_id})

        return render(
            request,
            'admin/reset_password.html',
            context={'form': form, 'user': user}
        )


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
