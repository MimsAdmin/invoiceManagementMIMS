# vercel_app.py
import os
import sys

# Add the project directory to the sys.path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoiceManagement.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
app = application