"""
URL configuration for invoiceManagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
import os

def debug_storage(_):
    return JsonResponse({
        "DEFAULT_FILE_STORAGE": getattr(settings, "DEFAULT_FILE_STORAGE", "filesystem"),
        "USE_R2": getattr(settings, "USE_R2", None),
        "MEDIA_URL": settings.MEDIA_URL,
        "HAS_AWS_KEY": bool(os.getenv("AWS_ACCESS_KEY_ID")),
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("landing.urls")),
    path('auth/', include('authen.urls')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path("log/", include("log.urls", namespace="log")),
] 

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    static_dirs = getattr(settings, "STATICFILES_DIRS", [])
    document_root = static_dirs[0] if static_dirs else settings.STATIC_ROOT
    urlpatterns += static(settings.STATIC_URL, document_root=document_root)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)