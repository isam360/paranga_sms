from django.urls import path
from . import views

app_name = "results"

urlpatterns = [
    path("upload/<uuid:token>/", views.upload_results_view, name="upload_results"),
]
