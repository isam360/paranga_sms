import random
import string
import logging
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, OtpTokenSerializer
from django_ratelimit.decorators import ratelimit
from .models import User, OtpToken
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import F
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed


# Setting up a logger for logging information
logger = logging.getLogger(__name__)

# for dynamic routing
route = "http://127.0.0.1:8000"

def generate_hex_otp(length=6):
    """
    Generate a random hexadecimal OTP of the specified length.

    Parameters:
    length (int): Length of the OTP to generate. Default is 6.

    Returns:
    str: A randomly generated hexadecimal OTP.
    """
    hex_chars = string.ascii_letters + string.digits
    return ''.join(random.choices(hex_chars, k=length))

@ratelimit(key='ip', rate='10/m', method='POST', block=True)
@api_view(['POST'])
def register_view(request):
    """
    Handles user registration and sends an OTP for email verification.

    Parameters:
    request (Request): The incoming request containing user registration data.

    Returns:
    Response: A response indicating the success or failure of registration.
    """
    if request.user.is_authenticated:
        return Response({'detail': 'You are already authenticated. Please log out to register a new account.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Get the user registration data from the request
    username = request.data.get('username')
    email = request.data.get('email')

    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response({'error': 'This username is already taken. Please choose another one.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response({'error': 'This email is already registered. Please use a different email address.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Proceed with the registration if validation passed
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Generate OTP
        otp_code = generate_hex_otp(6)
        OtpToken.objects.create(user=user, otp_code=otp_code,
                                 otp_expires_at=timezone.now() + timezone.timedelta(minutes=5))

        # Email content for OTP verification
        html_message = render_to_string('emails/verification_email.html', {
            'username': user.username,
            'otp_code': otp_code,
            'verification_url': f"{route}/verify-email/"
        })

        subject = "Email Verification"
        user.email_user(subject=subject, message='', html_message=html_message)

        # Return success response
        return Response({'message': 'Registration successful! Please check your email for the OTP to verify your account.'},
                        status=status.HTTP_201_CREATED)

    # If serializer is not valid, return the error details
    return Response({'error': 'There were errors in your registration data.', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_otp_history_view(request):
    """
    Retrieve OTP history for the authenticated user.

    Parameters:
    request (Request): The incoming request.

    Returns:
    Response: A response containing the user's OTP history.
    """
    user = request.user
    otp_tokens = OtpToken.objects.filter(user=user).order_by('-otp_created_at')
    serializer = OtpTokenSerializer(otp_tokens, many=True)
    return Response(serializer.data)
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@api_view(['POST'])
def login_view(request):
    """
    Handles user login and returns access and refresh tokens.

    Parameters:
    request (Request): The incoming request containing user login data.

    Returns:
    Response: A response containing login status and tokens.
    """
    # Try to deserialize the incoming request data
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {'non_field_errors': ["We don't have a registered user with that username."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.is_active:
            return Response({'non_field_errors': ['Account is not activated.']}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": f"Welcome back, {user.username}!",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })

    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Handles user logout by blacklisting the refresh token.

    Parameters:
    request (Request): The incoming request containing the refresh token.

    Returns:
    Response: A response indicating the logout status.
    """
    try:
        refresh_token = request.data.get('refresh')
        RefreshToken(refresh_token).blacklist()
        return Response({"message": "You have been logged out successfully."}, 
                        status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({"error": "Logout failed due to an error."}, status=status.HTTP_400_BAD_REQUEST)

@ratelimit(key='ip', rate='10/m', method='GET', block=True)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_view(request):
    """
    Retrieves the authenticated user's profile information.

    Parameters:
    request (Request): The incoming request.

    Returns:
    Response: A response containing the user's profile data.
    """
    user = request.user
    serializer = UserProfileSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@ratelimit(key='ip', rate='10/m', method='PUT', block=True)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """
    Updates the authenticated user's profile information.

    Parameters:
    request (Request): The incoming request containing updated profile data.

    Returns:
    Response: A response indicating the success or failure of the profile update.
    """
    user = request.user
    serializer = UserProfileSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Profile updated successfully',
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            **serializer.data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_social_media_links_view(request):
    """
    Updates the authenticated user's social media links.

    Parameters:
    request (Request): The incoming request containing social media URLs.

    Returns:
    Response: A response indicating the success of the update.
    """
    user = request.user
    facebook_link = request.data.get('facebook_url')
    twitter_link = request.data.get('twitter_url')
    linkedin_link = request.data.get('linkedin_url')
    instagram_link = request.data.get('instagram_url')

    # Update the social media links
    user.facebook_link = facebook_link
    user.twitter_link = twitter_link
    user.linkedin_link = linkedin_link
    user.instagram_link = instagram_link
    user.save()

    return Response({"detail": "Social media links updated successfully."}, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account_view(request):
    """
    Handles account deletion for the authenticated user.

    Parameters:
    request (Request): The incoming request.

    Returns:
    Response: A response indicating the success of account deletion.
    """
    user = request.user
    user.delete()
    logger.info(f"User {user.username} has deleted their account.")
    return Response({"message": "Your account has been deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def verify_otp_view(request, username):
    """
    Verifies the OTP for account activation.

    Parameters:
    request (Request): The incoming request containing the OTP code.
    username (str): The username of the user.

    Returns:
    Response: A response indicating the success or failure of OTP verification.
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'No user found with that username.'}, status=status.HTTP_404_NOT_FOUND)

    otp_code = request.data.get('otp_code')

    if OtpToken.objects.filter(user=user, attempts__gte=3).exists():
        return Response({'error': 'Too many failed attempts. Please request a new OTP.'}, 
                        status=status.HTTP_429_TOO_MANY_REQUESTS)

    try:
        otp_token = OtpToken.objects.get(user=user, otp_code=otp_code)
    except OtpToken.DoesNotExist:
        OtpToken.objects.filter(user=user).update(attempts=F('attempts') + 1)
        return Response({'error': 'The OTP you entered is invalid.'}, status=status.HTTP_400_BAD_REQUEST)

    if otp_token.otp_expires_at < timezone.now():
        return Response({'error': 'The OTP has expired. Please request a new one.'}, 
                        status=status.HTTP_400_BAD_REQUEST)

    user.is_active = True
    user.save()
    otp_token.delete()

    return Response({
        'message': 'Your account has been verified successfully!',
        'login_url': "/"
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def resend_otp_view(request):
    """
    Resends the OTP for email verification to the user.

    Parameters:
    request (Request): The incoming request containing the username.

    Returns:
    Response: A response indicating the success or failure of the resend action.
    """
    username = request.data.get('username')
    try:
        user = User.objects.get(username=username)
        if user.is_active:
            return Response({'message': 'Your account is already verified. You can log in.'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        otp_code = generate_hex_otp(6)
        OtpToken.objects.create(user=user, otp_code=otp_code, 
                                 otp_expires_at=timezone.now() + timezone.timedelta(minutes=5))

        html_message = render_to_string('emails/verification_email.html', {
            'username': user.username,
            'otp_code': otp_code,
            'verification_url': f"{route}/verify-email/"
        })

        subject = "Resend OTP - Email Verification"
        user.email_user(subject=subject, message='', html_message=html_message)

        return Response({'message': 'A new OTP has been sent to your email.'}, 
                        status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'No user found with that username.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def password_reset_view(request):
    """
    Requests a password reset by sending a reset link to the user's email.

    Parameters:
    request (Request): The incoming request containing the email address.

    Returns:
    Response: A response indicating the success or failure of the password reset request.
    """
    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)
        reset_code = generate_hex_otp(6)
        OtpToken.objects.create(user=user, otp_code=reset_code, 
                                 otp_expires_at=timezone.now() + timezone.timedelta(minutes=10))

        html_message = render_to_string('emails/password_reset_email.html', {
            'username': user.username,
            'reset_code': reset_code,
            'reset_url': f"{route}/password-reset/confirm/"
        })

        subject = "Password Reset Request"
        user.email_user(subject=subject, message='', html_message=html_message)

        return Response({'message': 'A password reset link has been sent to your email.'}, 
                        status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'No user found with that email address.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def password_reset_confirm_view(request, username):
    """
    Confirms the password reset using the OTP and updates the user's password.

    Parameters:
    request (Request): The incoming request containing the OTP code and new password.
    username (str): The username of the user.

    Returns:
    Response: A response indicating the success or failure of the password reset confirmation.
    """
    otp_code = request.data.get('otp_code')
    new_password = request.data.get('new_password')

    try:
        user = User.objects.get(username=username)
        otp_token = OtpToken.objects.get(user=user, otp_code=otp_code)

        if otp_token.otp_expires_at < timezone.now():
            return Response({'error': 'The OTP has expired. Please request a new password reset.'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        html_message = render_to_string('emails/password_reset_confirmation.html', {
            'username': user.username,
        })

        subject = "Password Reset Confirmation"
        user.email_user(subject=subject, message='', html_message=html_message)

        otp_token.delete()

        return Response({'message': 'Your password has been reset successfully! You can now log in.'}, 
                        status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'No user found with that username.'}, status=status.HTTP_404_NOT_FOUND)
    except OtpToken.DoesNotExist:
        return Response({'error': 'Invalid or expired OTP. Please request a new password reset.'}, 
                        status=status.HTTP_400_BAD_REQUEST)

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Changes the user's password if the old password is correct.

    Parameters:
    request (Request): The incoming request containing old and new passwords.

    Returns:
    Response: A response indicating the success or failure of the password change.
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not user.check_password(old_password):
        return Response({'error': 'The old password you entered is incorrect.'}, 
                        status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    html_message = render_to_string('emails/password_change_confirmation.html', {
        'username': user.username,
    })

    subject = "Password Change Confirmation"
    user.email_user(subject=subject, message='', html_message=html_message)

    return Response({'message': 'Your password has been changed successfully! You can now log in with the new password.'}, 
                    status=status.HTTP_200_OK)
