# /api/create_superuser.py
import os, sys, traceback
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "invoiceManagement.settings")

try:
    application = get_wsgi_application()
except Exception:
    def handler(request, response):
        response.status_code = 500
        response.send("❌ Django init failed:\n" + traceback.format_exc())
else:
    from django.contrib.auth import get_user_model

    def handler(request, response):
        try:
            REQUIRED_TOKEN = os.getenv("ADMIN_SETUP_TOKEN")
            given = request.args.get("token") if hasattr(request, "args") else None
            if REQUIRED_TOKEN and given != REQUIRED_TOKEN:
                response.status_code = 403
                response.send("Forbidden: invalid token")
                return

            User = get_user_model()
            username = os.getenv("ADMIN_USERNAME", "MIMSadmin")
            email    = os.getenv("ADMIN_EMAIL", "admin@example.com")
            password = os.getenv("ADMIN_PASSWORD", "HappyWork1905")

            u, created = User.objects.get_or_create(username=username, defaults={
                "email": email, "is_staff": True, "is_superuser": True
            })
            if not created:
                u.email = email
                u.is_staff = True
                u.is_superuser = True
                u.set_password(password)
                u.save()
                response.status_code = 200
                response.send("✅ Superuser password reset & ensured staff/superuser")
            else:
                u.set_password(password)
                u.save()
                response.status_code = 200
                response.send("✅ Superuser created")
        except Exception:
            response.status_code = 500
            response.send("❌ Handler failed:\n" + traceback.format_exc())
