from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from tests.helpers import create_test_user


class JWTAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(username='jwtuser', password='securepass123')

    def test_login_success(self):
        response = self.client.post('/api/users/login/', {
            'username': 'jwtuser',
            'password': 'securepass123',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        response = self.client.post('/api/users/login/', {
            'username': 'jwtuser',
            'password': 'wrongpassword',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_user(self):
        response = self.client.post('/api/users/login/', {
            'username': 'nobody',
            'password': 'securepass123',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_success(self):
        login = self.client.post('/api/users/login/', {
            'username': 'jwtuser',
            'password': 'securepass123',
        }, format='json')
        response = self.client.post('/api/users/refresh/', {
            'refresh': login.data['refresh'],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_invalid_token(self):
        response = self.client.post('/api/users/refresh/', {
            'refresh': 'invalid-token',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_token_grants_api_access(self):
        login = self.client.post('/api/users/login/', {
            'username': 'jwtuser',
            'password': 'securepass123',
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get('/api/users/profile/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
