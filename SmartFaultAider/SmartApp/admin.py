from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.http import HttpResponseRedirect
# Simple analytics dashboard view
@staff_member_required
def analytics_dashboard(request):
    total_chats = ChatLog.objects.count()
    flagged = ChatLog.objects.filter(feedback='flag').count()
    not_helpful = ChatLog.objects.filter(feedback='bad').count()
    with_attachments = ChatLog.objects.exclude(attachment='').exclude(attachment=None).count()
    return render(request, 'admin/analytics_dashboard.html', {
        'total_chats': total_chats,
        'flagged': flagged,
        'not_helpful': not_helpful,
        'with_attachments': with_attachments,
    })
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
from .models import IssueLog, ChatLog, UserProfile, Asset
from import_export import resources
from import_export.admin import ImportExportModelAdmin
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_input', 'bot_response', 'feedback', 'timestamp']
    list_filter = ['feedback', 'timestamp', 'user']
    search_fields = ['user_input', 'bot_response']


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
            path('analytics-dashboard/', self.admin_site.admin_view(analytics_dashboard), name='analytics_dashboard'),
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


class AssetResource(resources.ModelResource):
    class Meta:
        model = Asset
        import_id_fields = ('serial_number',)
        fields = ('id', 'name', 'category', 'serial_number', 'status', 'department', 'user', 'shared')

@admin.register(Asset)
class AssetAdmin(ImportExportModelAdmin):
    resource_class = AssetResource
    list_display = ('name', 'category', 'serial_number', 'status', 'department', 'user', 'shared')
    list_filter = ('category', 'status', 'department', 'shared')
    search_fields = ('name', 'serial_number', 'user', 'department')


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(IssueLog)
admin.site.register(ChatLog, ChatLogAdmin)
admin.site.register(UserProfile)