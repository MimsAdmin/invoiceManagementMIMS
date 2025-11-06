# authen/urls.py
from django.urls import path
from . import views

app_name = "authen"

urlpatterns = [
    path("sign-in/", views.sign_in, name="sign-in"),
    path("sign-up/", views.sign_up, name="sign-up"),
    path("logout/", views.sign_out, name="logout"),
]
