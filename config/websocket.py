from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Import your custom middleware and routing
from communications.middleware import QueryAuthMiddleware
import communications.routing

# The WebSocket application handles connection using our custom middleware
websocket_application = QueryAuthMiddleware(
    URLRouter(
        communications.routing.websocket_urlpatterns
    )
)
