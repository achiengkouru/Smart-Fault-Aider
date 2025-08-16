from django.contrib.auth.models import User
# User profile view
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms

from .models import ChatLog, IssueLog, UserProfile, Asset
from .asset_assistant import asset_assistant_view
from django.shortcuts import render
# ...existing code...

class ProfileForm(forms.ModelForm):
    profile_pic = forms.ImageField(required=False, label="Profile Picture")
    class Meta:
        model = User
        fields = ['email']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})

@login_required
def user_profile(request):
    user = request.user
    chatlogs = ChatLog.objects.filter(user=user)
    total_chats = chatlogs.count()
    flagged = chatlogs.filter(feedback='flag').count()
    not_helpful = chatlogs.filter(feedback='bad').count()
    helpful = chatlogs.filter(feedback='good').count()
    with_attachments = chatlogs.exclude(attachment='').exclude(attachment=None).count()

    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            profile_pic = form.cleaned_data.get('profile_pic')
            if profile_pic:
                profile.profile_pic = profile_pic
                profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile')
    else:
        form = ProfileForm(instance=user)

    context = {
        'user': user,
        'form': form,
        'profile': profile,
        'total_chats': total_chats,
        'flagged': flagged,
        'not_helpful': not_helpful,
        'helpful': helpful,
        'with_attachments': with_attachments,
    }
    return render(request, 'profile.html', context)
# FAQ view
from django.views.decorators.cache import cache_page

@cache_page(60 * 60)  # Cache for 1 hour
def faq(request):
    return render(request, 'faq.html')


import os
import requests
from dotenv import load_dotenv
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import mail_admins
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
import markdown
from .forms import ChatForm, AssetForm
from .models import ChatLog, IssueLog, Asset
from difflib import SequenceMatcher
# File extraction imports
import mimetypes
from PIL import Image
import pytesseract
import pdfplumber

# Helper function to find similar past issues
def find_similar_issue(user_question, threshold=0.7):
    all_issues = IssueLog.objects.all()
    for issue in all_issues:
        similarity = SequenceMatcher(None, user_question.lower(), issue.issue.lower()).ratio()
        if similarity > threshold:
            return issue
    return None

# signup view
def homepage(request):
    return render(request, 'index/homepage.html')

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-2.0-flash" 
GEMINI_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}'

# signup view
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def forgot_password(request):
    return render(request, 'registration/forgot_password.html')

def get_gemini_response(prompt):
    system_instruction = (
        "You are an expert assistant. Only answer questions related to software, hardware, or networking. "
        "If the question is outside these topics, politely refuse to answer.\n\n"
    )
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": system_instruction + prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_URL, headers=headers, json=data)
        response_json = response.json()
        print("Gemini Response:", response_json)
        return response_json['candidates'][0]['content']['parts'][0]['text']

    except Exception as e:
        print("Gemini API error:", e)
        return "Sorry, I'm having trouble processing your request."


@login_required(login_url='/accounts/login/')
def chatbot_view(request):
    form = ChatForm()
    response = ''
    chatlog_id = None
    if request.method == 'POST':
        # Handle feedback submission
        if 'feedback_for' in request.POST and 'feedback' in request.POST:
            chatlog_id = request.POST.get('feedback_for')
            feedback = request.POST.get('feedback')
            try:
                chatlog = ChatLog.objects.get(id=chatlog_id, user=request.user)
                chatlog.feedback = feedback
                chatlog.save()
                # Notify admins if flagged
                if feedback == 'flag':
                    mail_admins(
                        subject='Chat flagged by user',
                        message=f'User {request.user.username} flagged a chat (ID: {chatlog_id}).\n\nUser Input: {chatlog.user_input}\nBot Response: {chatlog.bot_response}',
                    )
                response = "<span style='color:green;'>Thank you for your feedback!</span>"
            except ChatLog.DoesNotExist:
                response = "<span style='color:red;'>Could not save feedback.</span>"

        else:
            form = ChatForm(request.POST, request.FILES)
            if form.is_valid():
                question = form.cleaned_data['question']
                attachment = form.cleaned_data.get('attachment')
                extracted_text = ''
                # Extract text from attachment if present
                if attachment:
                    content_type = attachment.content_type
                    try:
                        if content_type in ['image/jpeg', 'image/png', 'image/gif']:
                            image = Image.open(attachment)
                            extracted_text = pytesseract.image_to_string(image)
                            if extracted_text.strip():
                                extracted_text = f"\n\n[Extracted from image]:\n{extracted_text.strip()}"
                        elif content_type == 'application/pdf':
                            with pdfplumber.open(attachment) as pdf:
                                pdf_text = ''
                                for page in pdf.pages:
                                    pdf_text += page.extract_text() or ''
                                if pdf_text.strip():
                                    extracted_text = f"\n\n[Extracted from PDF]:\n{pdf_text.strip()}"
                    except Exception as e:
                        extracted_text = f"\n\n[Could not extract file text: {str(e)}]"

                # Append extracted text to question
                full_prompt = question + (extracted_text if extracted_text else '')

                # Check for similar past issues
                similar_issue = find_similar_issue(full_prompt)
                if similar_issue:
                    response = markdown.markdown(
                        f"**A similar issue was previously resolved:**\n\n"
                        f"**Issue:** {similar_issue.issue}\n\n"
                        f"**Solution:** {similar_issue.solution}"
                    )
                    chatlog = ChatLog.objects.create(user=request.user, user_input=full_prompt, bot_response=similar_issue.solution, attachment=attachment)
                    chatlog_id = chatlog.id
                else:
                    # Get Gemini's raw Markdown response
                    raw_response = get_gemini_response(full_prompt)
                    response = markdown.markdown(raw_response)
                    # Save user input and raw bot response (for history/logs)
                    chatlog = ChatLog.objects.create(user=request.user, user_input=full_prompt, bot_response=raw_response, attachment=attachment)
                    chatlog_id = chatlog.id

    return render(request, 'chatbot/chat.html', {
        'form': form,
        'response': response,  # HTML-safe version
        'chatlog_id': chatlog_id,
    })

    return render(request, 'chatbot/chat.html', {
        'form': form,
        'response': response  # HTML-safe version
    })

# View for user chat history
@login_required(login_url='/accounts/login/')
def chat_history(request):
    user_chats = ChatLog.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'chatbot/chat_history.html', {'user_chats': user_chats})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def settings_view(request):
    return render(request, 'settings.html')

@login_required
def asset_list(request):
    assets = Asset.objects.all().order_by('category', 'name')
    return render(request, 'assets/asset_list.html', {'assets': assets})

@login_required
def asset_add(request):
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('asset_list')
    else:
        form = AssetForm()
    return render(request, 'assets/asset_form.html', {'form': form, 'action': 'Add'})

@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            form.save()
            return redirect('asset_list')
    else:
        form = AssetForm(instance=asset)
    return render(request, 'assets/asset_form.html', {'form': form, 'action': 'Edit'})

@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    return render(request, 'assets/asset_detail.html', {'asset': asset})

@login_required
def clear_chats(request):
    if request.method == 'POST':
        ChatLog.objects.filter(user=request.user).delete()
        messages.success(request, 'All chats cleared!')
    return redirect('chatbot')

@login_required
def clear_asset_chats(request):
    if request.method == 'POST':
        if 'asset_messages' in request.session:
            request.session['asset_messages'] = []
        messages.success(request, 'All asset assistant chats cleared!')
    return redirect('asset_assistant')

@login_required
def asset_debug_view(request):
    assets = Asset.objects.all().order_by('category', 'department', 'name')
    return render(request, 'assets/asset_debug.html', {'assets': assets})


