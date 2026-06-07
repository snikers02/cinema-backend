from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from asgiref.sync import async_to_sync
from apps.users.middleware import get_user, JWTAuthMiddleware
from tests.helpers import create_test_user


class GetUserTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='wsuser')

    def test_valid_token_returns_user(self):
        token = str(AccessToken.for_user(self.user))
        result = async_to_sync(get_user)(token)
        self.assertEqual(result.id, self.user.id)

    def test_invalid_token_returns_anonymous(self):
        result = async_to_sync(get_user)('bad-token')
        self.assertIsInstance(result, AnonymousUser)

    def test_expired_token_returns_anonymous(self):
        result = async_to_sync(get_user)('')
        self.assertIsInstance(result, AnonymousUser)


class JWTAuthMiddlewareTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='middlewareuser')

    async def _run_middleware(self, query_string):
        captured = {}

        async def app(scope, receive, send):
            captured['user'] = scope['user']

        middleware = JWTAuthMiddleware(app)
        scope = {'query_string': query_string.encode()}
        await middleware(scope, None, None)
        return captured['user']

    def test_middleware_with_valid_token(self):
        token = str(AccessToken.for_user(self.user))
        user = async_to_sync(self._run_middleware)(f'token={token}')
        self.assertEqual(user.id, self.user.id)

    def test_middleware_without_token(self):
        user = async_to_sync(self._run_middleware)('')
        self.assertIsInstance(user, AnonymousUser)

    def test_middleware_with_invalid_token(self):
        user = async_to_sync(self._run_middleware)('token=not-valid')
        self.assertIsInstance(user, AnonymousUser)
