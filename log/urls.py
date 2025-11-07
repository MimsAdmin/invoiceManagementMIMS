from django.urls import path
from . import views

app_name = "log"

urlpatterns = [
    path("", views.page, name="page"),
    path("api/entries/", views.api_entries, name="api-entries"),
    path("api/download/", views.api_download, name="api-download"),
]
