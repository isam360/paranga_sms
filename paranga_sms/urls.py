from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from landingpage.views import landing_page , help_page

urlpatterns = [
    # path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('', landing_page, name='landing'),
    path('help/', help_page, name='help_page'),
   
    path('admin/', admin.site.urls),


    # Include default auth URLs (login/logout/password reset)
    path('accounts/', include('django.contrib.auth.urls')),

    # Your API and results routes
    path('api/students/', include('students.urls')),
    path('api/teachers/', include('teachers.urls')),
    path('api/announcements/', include('announcements.urls')), 
    path("results/", include("results.urls")), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
