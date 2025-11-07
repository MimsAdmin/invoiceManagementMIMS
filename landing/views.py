# landing/views.py
from django.shortcuts import render

def landing_home(request):
    return render(request, "landing.html")

def pak_rino(request):
    return render(request, "pakRino.html")

def pak_bas(request):
    return render(request, "pakBas.html")

def pak_budi(request):
    return render(request, "pakBudi.html")
