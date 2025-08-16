# SmartApp/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

# User profile with profile picture
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

# Automatically create or update UserProfile when User is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        try:
            instance.userprofile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)

# Model to store past issues and solutions
class IssueLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    issue = models.TextField()
    solution = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.issue[:50]}..."

class ChatLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_input = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(default=now)
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    FEEDBACK_CHOICES = [
        ("good", "👍 Helpful"),
        ("bad", "👎 Not Helpful"),
        ("flag", "⚠️ Flag/Report")
    ]
    feedback = models.CharField(max_length=10, choices=FEEDBACK_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.timestamp}: {self.user_input[:30]}..."

class Asset(models.Model):
    CATEGORY_CHOICES = [
        ('PC', 'Computer'),
        ('UPS', 'UPS'),
        # Add more if needed
    ]
    STATUS_CHOICES = [
        ('WORKING', 'Working'),
        ('FAULTY', 'Faulty'),
        ('UNDER_REPAIR', 'Under Repair'),
        ('RETIRED', 'Retired'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    serial_number = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    department = models.CharField(max_length=100)
    user = models.CharField(max_length=100, blank=True)
    shared = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.serial_number}"

