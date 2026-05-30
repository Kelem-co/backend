from accounts.jwt_views import CookieTokenRefreshView
from accounts.jwt_views import LogoutView
from accounts.jwt_views import OrganizationApprovalMagicLinkExchangeView
from accounts.jwt_views import OrganizationAwareTokenObtainPairView
from accounts.jwt_views import ParentOTPRequestView
from accounts.jwt_views import ParentOTPVerifyView
from django.urls import path
from django.urls import re_path
from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [
    path(
        "jwt/create/",
        OrganizationAwareTokenObtainPairView.as_view(),
        name="jwt-create",
    ),
    path(
        "organization-approval/exchange/",
        OrganizationApprovalMagicLinkExchangeView.as_view(),
        name="organization-approval-exchange",
    ),
    path(
        "otp/request/",
        ParentOTPRequestView.as_view(),
        name="parent-otp-request",
    ),
    path(
        "otp/verify/",
        ParentOTPVerifyView.as_view(),
        name="parent-otp-verify",
    ),
    re_path(r"^jwt/refresh/?", CookieTokenRefreshView.as_view(), name="jwt-refresh"),
    re_path(r"^jwt/verify/?", TokenVerifyView.as_view(), name="jwt-verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
