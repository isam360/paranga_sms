from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError

class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser.

    This model represents a user in the application and includes
    additional fields like email, role, and profile information.

    Attributes:
        email (EmailField): The email address of the user, must be unique.
        role_choices (tuple): A tuple of choices for user roles.
        role (CharField): The role assigned to the user, chosen from role_choices.
        first_name (CharField): The first name of the user.
        last_name (CharField): The last name of the user.
        bio (TextField): A short biography or description of the user.
        profile_picture (ImageField): An optional field to upload a profile picture.
        whatsapp_number (CharField): User's WhatsApp number, must start with a country code.
        facebook_link (URLField): URL to the user's Facebook profile.
        instagram_link (URLField): URL to the user's Instagram profile.
        twitter_link (URLField): URL to the user's Twitter profile.
        website (URLField): URL to the user's personal website.
    """
    email = models.EmailField(unique=True)
    role_choices = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    
    role = models.CharField(max_length=20, choices=role_choices, default='user')
    first_name = models.CharField(max_length=30, blank=True)  
    last_name = models.CharField(max_length=30, blank=True)  
    bio = models.TextField(blank=True)                        
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)  
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True, help_text="Include country code, e.g., +1234567890")
    facebook_link = models.URLField(blank=True, null=True, help_text="Your Facebook profile URL")
    instagram_link = models.URLField(blank=True, null=True, help_text="Your Instagram profile URL")
    twitter_link = models.URLField(blank=True, null=True, help_text="Your Twitter profile URL")
    website = models.URLField(blank=True, null=True, help_text="Your personal website URL")

    def clean(self):
        """
        Validate the WhatsApp number format.
        """
        if self.whatsapp_number and not self.whatsapp_number.startswith('+'):
            raise ValidationError('WhatsApp number must start with a country code (e.g., +1234567890).')

    def __str__(self):
        """
        String representation of the User instance.

        Returns:
            str: The username of the user.
        """
        return self.username


class OtpToken(models.Model):
    """
    Model representing an OTP (One-Time Password) for user verification.

    This model stores OTP codes generated for users during the registration
    and verification process. It tracks the creation time, expiration, and
    number of attempts to use the OTP.

    Attributes:
        user (ForeignKey): A reference to the User model, linked to a specific user.
        otp_code (CharField): The generated OTP code.
        otp_created_at (DateTimeField): The timestamp when the OTP was created.
        otp_expires_at (DateTimeField): The timestamp when the OTP expires.
        attempts (IntegerField): A counter to track how many times the OTP has been attempted.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    otp_created_at= models.DateTimeField(auto_now_add=True) # referencial  date post in database

    otp_expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)  # Track attempts

    def __str__(self):
        """
        String representation of the OtpToken instance.

        Returns:
            str: A string combining the username and OTP code.
        """
        return f"{self.user.username} - {self.otp_code}"
