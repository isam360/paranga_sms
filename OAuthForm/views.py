from django.shortcuts import render , redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


def home(request):
    return render(request,'home.html',{})
    
def index(request):
    return render(request,'main.html',{})
   
def profile(request):
    return render(request,'profile.html',{})
         
def registerView(request):
    return render(request,'auth/register.html',{})

def loginView(request):
    return render(request,'auth/login.html',{})

def emailVerification(request):
    return render(request,'auth/email-verification-form.html',{})

def passwordReset(request):
    return render(request,'auth/password-reset-form.html',{})

def passwordResetConfrim(request):
    return render(request,'auth/password-reset-confirm.html',{})


def logoutView(request):
    logout(request)   
    return render(request,'logout_confirm.html')


    