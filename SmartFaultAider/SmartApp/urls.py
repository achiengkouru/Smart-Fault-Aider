# SmartApp/urls.py

from django.urls import path, include

from .views import (
    chatbot_view,
    clear_chats,
    clear_asset_chats,
    signup,
    forgot_password,
    homepage,
    chat_history,
    faq,
    user_profile,
    settings_view,
    asset_list,
    asset_add,
    asset_edit,
    asset_detail,
    asset_debug_view,
)
from .asset_assistant import asset_assistant_view

urlpatterns = [
    path('', homepage, name='homepage'),
    path('chatbot/', chatbot_view, name='chatbot'),
    path('clear-chats/', clear_chats, name='clear_chats'),
    path('chat-history/', chat_history, name='chat_history'),
    path('faq/', faq, name='faq'),
    path('accounts/signup/', signup, name='signup'),
    path('forgot_password', forgot_password, name='forgot_password'),
    path('profile/', user_profile, name='user_profile'),
    path('settings/', settings_view, name='settings'),
    path('assets/', asset_list, name='asset_list'),
    path('assets/add/', asset_add, name='asset_add'),
    path('assets/<int:pk>/edit/', asset_edit, name='asset_edit'),
    path('assets/<int:pk>/', asset_detail, name='asset_detail'),
    path('asset-assistant/', asset_assistant_view, name='asset_assistant'),
    path('clear-asset-chats/', clear_asset_chats, name='clear_asset_chats'),
    path('assets/debug/', asset_debug_view, name='asset_debug'),
]
