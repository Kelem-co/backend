from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


@database_sync_to_async
def get_user_from_token(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class QueryAuthMiddleware:
    """
    Custom middleware that extracts the token from the query string
    and authenticates the user.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        token_key = query_params.get("token", [None])[0]

        if token_key:
            scope["user"] = await get_user_from_token(token_key)
        elif "user" not in scope:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)
