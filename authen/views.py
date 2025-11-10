# authen/views.py
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.db.models import Q

def sign_in(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        user = User.objects.filter(email__iexact=email).first()
        if user:
            user = authenticate(request, username=user.username, password=password)

        if user is None:
            messages.error(request, "Email or password is incorrect.")
            return render(request, "signIn.html", {})

        profile = getattr(user, "profile", None)
        if not user.is_active or (profile and profile.approval_status != "APPROVED"):
            if profile and profile.approval_status == "REJECTED":
                messages.error(request, "Your registration has been rejected by the admin. Please contact the administrator.")
            else:
                messages.warning(request, "Your account has not yet been approved by the admin")
            return render(request, "signIn.html", {})

        login(request, user)
        return redirect('dashboard:home')

    return render(request, "signIn.html", {})

def sign_up(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        if not email or not password1:
            messages.error(request, "Email and password are required.")
            return render(request, "signUp.html")

        if password1 != password2:
            messages.error(request, "Password and confirmation password do not match.")
            return render(request, "signUp.html")

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, "signUp.html")

        username = email.split("@")[0]
        base_username = username
        i = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{i}"
            i += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            is_active=False,
        )

        messages.success(
            request,
            "Registration successful. Please wait for admin approval before you can log in."
        )
        return redirect("authen:sign-in")

    return render(request, "signUp.html")

def sign_out(request):
    logout(request)
    return redirect("landing")
