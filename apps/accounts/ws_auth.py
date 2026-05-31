from __future__ import annotations

from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


@database_sync_to_async
def _get_user_from_token(raw_token: str):
    authenticator = JWTAuthentication()
    validated_token = authenticator.get_validated_token(raw_token)
    return authenticator.get_user(validated_token)


class JwtQueryAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        current_user = scope.get("user")
        if current_user and getattr(current_user, "is_authenticated", False):
            return await self.inner(scope, receive, send)

        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]

        if token:
            try:
                scope["user"] = await _get_user_from_token(token)
            except (AuthenticationFailed, InvalidToken):
                scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)


def jwt_query_auth_middleware_stack(inner):
    return AuthMiddlewareStack(JwtQueryAuthMiddleware(inner))
