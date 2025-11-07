# landing/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing_home, name="landing"),
    path("pak-rino/", views.pak_rino, name="pak-rino"),
    path("pak-bas/", views.pak_bas, name="pak-bas"),
    path("pak-budi/", views.pak_budi, name="pak-budi"),
]
