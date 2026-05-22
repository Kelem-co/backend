import secrets

from accounts.email import BranchAdminInvitationEmail
from accounts.models import User
from branches.api.serializers import BranchAdminSerializer
from branches.api.serializers import BranchSerializer
from branches.models import Branch
from branches.models import BranchAdmin
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema_view
from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.access import scope_queryset_for_user

from .serializers import BranchAdminCompleteInvitationSerializer
from .serializers import BranchAdminInviteSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="school_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="Filter branches by School ID.",
            ),
            OpenApiParameter(
                name="school",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="Filter branches by School ID (alias).",
            ),
        ],
    ),
)
class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.select_related(
        "organization",
        "organization__owner",
        "school",
    )
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        queryset = scope_queryset_for_user(
            self.queryset,
            self.request.user,
            branch_lookup="self",
        )

        params = getattr(self.request, "query_params", self.request.GET)
        school_id = params.get(
            "school_id",
        ) or params.get("school")
        if school_id:
            queryset = queryset.filter(school_id=school_id)

        return queryset


class BranchAdminViewSet(viewsets.ModelViewSet):
    queryset = BranchAdmin.objects.select_related(
        "organization",
        "organization__owner",
        "branch",
        "user",
    )
    serializer_class = BranchAdminSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        queryset = scope_queryset_for_user(self.queryset, self.request.user)
        params = getattr(self.request, "query_params", self.request.GET)
        branch_id = params.get("branch")
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        return queryset


@extend_schema(request=BranchAdminInviteSerializer)
class BranchAdminInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BranchAdminInviteSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        email = data["email"]
        name = data["name"]
        father_name = data["father_name"]
        grandfather_name = data["grandfather_name"]
        role_title = data["role_title"]
        branch = data["branch"]

        random_password = secrets.token_urlsafe(16)
        user = User.objects.create_user(
            email=email,
            password=random_password,
            name=name,
            father_name=father_name,
            grandfather_name=grandfather_name,
            role=User.Role.BRANCH_ADMIN,
            is_active=False,
        )

        BranchAdmin.objects.create(
            organization=branch.organization,
            branch=branch,
            user=user,
            role_title=role_title,
            status=BranchAdmin.Status.INACTIVE,
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        path = f"complete-invitation/{uid}/{token}"

        email_obj = BranchAdminInvitationEmail(
            request,
            context={
                "user": user,
                "branch_name": branch.name,
                "invited_by": request.user.name,
                "url": path,
            },
        )
        email_obj.send([user.email])

        return Response(
            {"message": "Invitation sent successfully."},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(request=BranchAdminCompleteInvitationSerializer)
class BranchAdminCompleteInvitationView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = BranchAdminCompleteInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as err:
            raise ValidationError({"uid": "Invalid user ID."}) from err

        try:
            branch_admin = BranchAdmin.objects.get(
                user=user,
                status=BranchAdmin.Status.INACTIVE,
            )
        except BranchAdmin.DoesNotExist as err:
            raise ValidationError({"uid": "Invalid or expired invitation."}) from err

        if user.role != User.Role.BRANCH_ADMIN or user.is_active:
            raise ValidationError({"uid": "Invalid or expired invitation."})

        if not default_token_generator.check_token(user, token):
            raise ValidationError({"token": "Invalid or expired token."})

        user.set_password(new_password)
        user.is_active = True
        user.verified_at = timezone.now()
        user.save()

        branch_admin.status = BranchAdmin.Status.ACTIVE
        branch_admin.save(update_fields=["status", "updated_at"])

        return Response(
            {"message": "Password set and account activated successfully."},
            status=status.HTTP_200_OK,
        )
