import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')

# Import routing after settings
django_asgi_app = get_asgi_application()

from notifications import routing as notifications_routing
from videoconf import routing as videoconf_routing

# Combine all websocket urlpatterns
websocket_urlpatterns = (
    notifications_routing.websocket_urlpatterns
    + videoconf_routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
