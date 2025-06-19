# SmartApp/urls.py

from django.urls import path, include
from .views import chatbot_view, signup, forgot_password

urlpatterns = [
    path('', chatbot_view, name='chatbot'),
    path('accounts/signup/', signup, name='signup'),
    path('forgot_password', forgot_password, name='forgot_password'),
]
