from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, OtpToken
from django.utils import timezone

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    This serializer handles the registration of a new user by validating input data,
    ensuring unique emails, and creating a new user instance.

    Attributes:
        password1 (CharField): The password input for the user.
        password2 (CharField): A confirmation password input for validation.
    """
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def validate(self, data):
        """Validates the registration data."""
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists.")
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        """Creates a new user instance."""
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            is_active=False  # User is inactive until email verification
        )
        user.set_password(validated_data['password1'])  # Securely set the password
        user.save()
        return user
    
class OtpTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtpToken
        fields = ['otp_code', 'otp_created_at', 'otp_expires_at', 'attempts']

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.

    This serializer includes fields for the user's social media links and other profile data.
    """
    whatsapp_number = serializers.CharField(required=False, allow_blank=True)
    facebook_link = serializers.URLField(required=False, allow_blank=True)
    instagram_link = serializers.URLField(required=False, allow_blank=True)
    twitter_link = serializers.URLField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email','role', 'first_name', 'last_name', 'bio', 
                  'profile_picture', 'whatsapp_number', 'facebook_link', 
                  'instagram_link', 'twitter_link', 'website']
    
    def update(self, instance, validated_data):
        """Updates the user's profile information."""
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.role = validated_data.get('role', instance.role)

        # Handle profile picture if it exists
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data['profile_picture']

        # Update social media fields if provided
        instance.whatsapp_number = validated_data.get('whatsapp_number', instance.whatsapp_number)
        instance.facebook_link = validated_data.get('facebook_link', instance.facebook_link)
        instance.instagram_link = validated_data.get('instagram_link', instance.instagram_link)
        instance.twitter_link = validated_data.get('twitter_link', instance.twitter_link)
        instance.website = validated_data.get('website', instance.website)

        instance.save()
        return instance

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    This serializer handles the login process by authenticating the user credentials.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Validates the login credentials."""
        # Extract the username and password
        username = data['username']
        password = data['password']

        # Step 1: Check if the username exists
        user = authenticate(username=username, password=password)
        
        if not user:
            # Step 2: If user doesn't exist or password is incorrect
            # We first check if the username exists
            if not User.objects.filter(username=username).exists():
                raise serializers.ValidationError("We don't have a registered user with that username.")
            # If the user exists but authentication failed (wrong password)
            raise serializers.ValidationError("The password entered doesn't match the one on file for that username.")
        
        # Step 3: Check if the user is active
        if not user.is_active:
            raise serializers.ValidationError("Account is not activated.")
        
        return data  # Return the validated data instead of the User object


class OTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for OTP verification.

    This serializer validates the OTP provided by the user during the email verification process.
    """
    username = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, data):
        """Validates the OTP code."""
        try:
            user = User.objects.get(username=data['username'])
            otp_token = OtpToken.objects.filter(user=user).last()

            if otp_token and otp_token.otp_code == data['otp_code'] and otp_token.is_valid():
                user.is_active = True
                user.save()
                return user
            else:
                raise serializers.ValidationError("Invalid or expired OTP.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
