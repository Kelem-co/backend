from accounts.models import User
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .serializers import UserSerializer
from .serializers import UserUpdateSerializer


@extend_schema_view(
    list=extend_schema(
        responses={status.HTTP_200_OK: UserSerializer(many=True)},
    ),
    retrieve=extend_schema(
        responses={status.HTTP_200_OK: UserSerializer},
    ),
    update=extend_schema(
        request=UserUpdateSerializer,
        responses={status.HTTP_200_OK: UserSerializer},
    ),
    partial_update=extend_schema(
        request=UserUpdateSerializer,
        responses={status.HTTP_200_OK: UserSerializer},
    ),
)
class UserViewSet(
    RetrieveModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "id"
    permission_classes = [IsAuthenticated]

    def get_queryset(self, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        return self.queryset.filter(id=self.request.user.id)

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return UserUpdateSerializer
        return UserSerializer

    @extend_schema(
        responses={status.HTTP_200_OK: UserSerializer},
    )
    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)
