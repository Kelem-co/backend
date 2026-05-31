from accounts.ws_auth import jwt_query_auth_middleware_stack
from channels.routing import URLRouter
from messaging.routing import websocket_urlpatterns

websocket_application = jwt_query_auth_middleware_stack(
    URLRouter(websocket_urlpatterns),
)
