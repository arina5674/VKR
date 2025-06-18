"""
ASGI config for course project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course.settings')
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack  # Если нужна авторизация
from chat.routing import websocket_urlpatterns  # Импорт ваших WebSocket-путей


application = ProtocolTypeRouter({
    "http": django_asgi_app,  # Обычные HTTP-запросы
    "websocket": AuthMiddlewareStack(  # Если нужна аутентификация
        URLRouter(websocket_urlpatterns)  # Ваши WebSocket-маршруты
    ),
})
