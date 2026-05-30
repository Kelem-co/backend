from django.urls import re_path
from messaging.realtime import ThreadConsumer

websocket_urlpatterns = [
    re_path(r"^ws/chat/threads/(?P<thread_id>[0-9a-f-]+)/$", ThreadConsumer.as_asgi()),
]
