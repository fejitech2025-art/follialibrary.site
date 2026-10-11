import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.urls import path

# Initialize Django before importing application models.
django_asgi_app = get_asgi_application()

from clubs.consumers import ClubChatConsumer


websocket_routes = [
    path(
        "ws/clubs/<int:club_id>/",
        ClubChatConsumer.as_asgi(),
    ),
]

allowed_websocket_origins = {
    settings.FRONTEND_URL.rstrip("/"),
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
}

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": OriginValidator(
            AuthMiddlewareStack(
                URLRouter(websocket_routes)
            ),
            list(allowed_websocket_origins),
        ),
    }
)