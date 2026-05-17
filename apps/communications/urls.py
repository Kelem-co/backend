from django.urls import path, include
from rest_framework.routers import DefaultRouter

from communications.views import MessageViewSet, BroadcastView

router = DefaultRouter()

urlpatterns = [
    path("broadcast/", BroadcastView.as_view(), name="chat-broadcast"),
    path("<uuid:room_pk>/messages/", MessageViewSet.as_view({'get': 'list'}), name="room-messages-list"),
    path("<uuid:room_pk>/messages/<uuid:pk>/", MessageViewSet.as_view({'get': 'retrieve'}), name="room-messages-detail"),
]
