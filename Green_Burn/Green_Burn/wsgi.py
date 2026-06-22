"""
WSGI config for Green_Burn project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Green_Burn.settings')

# запускаем collectstatic автоматически при старте — нужно для Railway,
# так как статические файлы не сохраняются между деплоями
from django.core.management import call_command
try:
    call_command('collectstatic', '--noinput', verbosity=0)
except Exception:
    pass

application = get_wsgi_application()