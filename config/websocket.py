from accounts.ws_auth import JwtQueryAuthMiddlewareStack
from channels.routing import URLRouter
from messaging.routing import websocket_urlpatterns

websocket_application = JwtQueryAuthMiddlewareStack(
    URLRouter(websocket_urlpatterns),
)
