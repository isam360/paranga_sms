from django.urls import path
from .views import (
    index,
    home,
    profile,
    loginView,
    registerView,
    passwordResetConfrim,
    passwordReset,
    emailVerification,
    logoutView,
    

)

OAuthForm = "OAuthForm"

urlpatterns = [
    
    path('dashboard/',index,name='index'),
    path('profile/',profile,name='profile'),
    path('account/logout/',logoutView,name='logout'),
    path('',home,name='home'),
    path('login/',loginView,name='login'),
    path('register/',registerView,name='register'),
    path('verify-email/',emailVerification,name='verify-email'),
    path('password-reset/',passwordReset,name='forgot_password'),
    path('password-reset/confirm/',passwordResetConfrim,name='password-reset-confirm'),
    

]
