# apps/users/middleware.py
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user(token_key):
    try:
        token = AccessToken(token_key)
        user_id = token['user_id']
        return User.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token_key = None
        if "token=" in query_string:
            token_key = query_string.split("token=")[1]

        if token_key:
            scope['user'] = await get_user(token_key)
        else:
            scope['user'] = AnonymousUser()

        return await self.app(scope, receive, send)