# /api/create_superuser.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "invoiceManagement.settings")
application = get_wsgi_application()

from django.contrib.auth import get_user_model

def handler(request, response):
    REQUIRED_TOKEN = os.getenv("ADMIN_SETUP_TOKEN")
    given = request.args.get("token") if hasattr(request, "args") else None
    if REQUIRED_TOKEN and given != REQUIRED_TOKEN:
        response.status_code = 403
        response.send("Forbidden: invalid token")
        return

    User = get_user_model()
    username = os.getenv("ADMIN_USERNAME", "adminMIMS")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "HappyWork1905")

    if User.objects.filter(username=username).exists():
        response.status_code = 200
        response.send("⚠️ Superuser already exists")
        return

    User.objects.create_superuser(username=username, email=email, password=password)
    response.status_code = 200
    response.send("✅ Superuser created")
