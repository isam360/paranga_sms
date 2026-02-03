# from django.contrib import admin
# from django.utils.html import format_html
# from .models import User, OtpToken

# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     """
#     Custom admin class for the User model.

#     Enhances the admin interface with better data visualization,
#     including displaying the profile picture.
#     """
#     list_display = (
#         'username', 'email', 'role', 'first_name', 'last_name', 
#         'bio_snippet', 'profile_picture_preview', 'whatsapp_number'
#     )
#     list_filter = ('role', 'date_joined', 'is_active', 'is_staff')  # Filters
#     search_fields = ('username', 'email', 'first_name', 'last_name')  # Search bar
#     readonly_fields = ('date_joined', 'last_login')  # Read-only fields
#     fieldsets = (
#         ('Personal Information', {
#             'fields': ('username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture')
#         }),
#         ('Contact Information', {
#             'fields': ('whatsapp_number', 'facebook_link', 'instagram_link', 'twitter_link', 'website')
#         }),
#         ('Permissions and Status', {
#             'fields': ('role', 'is_staff', 'is_active', 'date_joined', 'last_login')
#         }),
#     )

#     def profile_picture_preview(self, obj):
#         """
#         Display a small preview of the profile picture in the admin panel.
#         """
#         if obj.profile_picture:
#             return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 50%;" />', obj.profile_picture.url)
#         return "No Image"

#     profile_picture_preview.short_description = "Profile Picture"

#     def bio_snippet(self, obj):
#         """
#         Show a snippet of the bio for better visualization.
#         """
#         return obj.bio[:50] + "..." if obj.bio and len(obj.bio) > 50 else obj.bio

#     bio_snippet.short_description = "Bio Snippet"


# @admin.register(OtpToken)
# class OtpTokenAdmin(admin.ModelAdmin):
#     """
#     Custom admin class for the OtpToken model.

#     Improves the admin interface for better OTP management.
#     """
#     list_display = ('user', 'otp_code', 'otp_created_at', 'otp_expires_at', 'attempts')
#     list_filter = ('otp_created_at', 'otp_expires_at')  # Filters by date
#     search_fields = ('user__username', 'otp_code')  # Search by username and OTP code
#     readonly_fields = ('otp_created_at',)


