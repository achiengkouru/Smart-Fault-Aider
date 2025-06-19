# SmartApp/models.py

from django.db import models
from django.utils.timezone import now

class ChatLog(models.Model):
    user_input = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.timestamp}: {self.user_input[:30]}..."
