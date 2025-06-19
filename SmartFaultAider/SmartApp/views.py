# SmartApp/views.py

import os
import requests
from dotenv import load_dotenv
from django.shortcuts import render
from .forms import ChatForm
from .models import ChatLog
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
import markdown

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
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
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

    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            question = form.cleaned_data['question']
            
            # Get Gemini's raw Markdown response
            raw_response = get_gemini_response(question)

            # Convert Markdown to HTML for display
            response = markdown.markdown(raw_response)

            # Save user input and raw bot response (for history/logs)
            ChatLog.objects.create(user_input=question, bot_response=raw_response)

    return render(request, 'chatbot/chat.html', {
        'form': form,
        'response': response  # HTML-safe version
    })
   

