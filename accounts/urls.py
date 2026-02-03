"""
This module defines the URL routing for the authentication API in a Django REST Framework application.
It maps various authentication-related views to their respective endpoints.
"""
from django.urls import path, include
from .views import (
    register_view,
    verify_otp_view,
    get_profile_view,
    update_profile_view,
    resend_otp_view,
    login_view,
    password_reset_view,
    password_reset_confirm_view,
    change_password_view,
    logout_view,
    get_otp_history_view,
    delete_account_view,
    update_social_media_links_view, 
    

 
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from django.conf.urls import handler404, handler500

handler404 = 'AuthApi.views.page_not_found_view'
handler500 = 'AuthApi.views.server_error_view'

 # Namespace for AuthApi
app_name = 'Auth' 

urlpatterns = [

    # User authentication and registration
    path('login/', login_view, name='login'),  
    path('register/', register_view, name='register'), 
    path('verify-otp/<str:username>/', verify_otp_view, name='verify_otp'),  
    path('resend-otp/', resend_otp_view, name='resend_otp'), 

    # Password Reset
    path('password-reset/', password_reset_view, name='password_reset'),  
    path('password-reset/<str:username>/', password_reset_confirm_view, name='password_reset_confirm'),  

    # User Profile Management
    path('profile/', get_profile_view, name='get_profile'),  
    path('profile/update/', update_profile_view, name='update_profile'),  

    # Update Social Media Links
    path('profile/social-media/update/', update_social_media_links_view, name='update_social_media'), 
    
    # Change Password
    path('change-password/', change_password_view, name='change_password'), 

    # Account Deletion
    path('delete-account/', delete_account_view, name='delete_account'), 
    
    # JWT Authentication (using SimpleJWT)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    
    # blacklisting tokens
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('otp-history/', get_otp_history_view, name='otp_history'),  
    
    # Logout
    path('logout/', logout_view, name='logout'),  


]
