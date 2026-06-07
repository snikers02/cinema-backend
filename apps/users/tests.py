from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tests.helpers import create_test_user

User = get_user_model()
PROFILE_URL = '/api/users/profile/me/'


class UserModelTests(TestCase):
    def setUp(self):
        self.user = create_test_user(
            username='testuser',
            email='testuser@test.com',
            bio='Test bio',
            is_pro=True,
            display_name='Test Name',
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'testuser@test.com')
        self.assertTrue(self.user.is_pro)
        self.assertEqual(self.user.bio, 'Test bio')

    def test_user_str_representation(self):
        self.assertEqual(str(self.user), 'testuser')

    def test_user_default_is_pro_false(self):
        user = create_test_user(username='regular')
        self.assertFalse(user.is_pro)

    def test_user_unique_email_constraint(self):
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='other',
                email=self.user.email,
                password='pass12345',
            )


class UserViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(username='existinguser')

    def test_register_user_success(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword123',
        }
        response = self.client.post('/api/users/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_user_missing_password(self):
        data = {'username': 'newuser2', 'email': 'new2@example.com'}
        response = self.client.post('/api/users/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_duplicate_username(self):
        data = {
            'username': 'existinguser',
            'email': 'unique@example.com',
            'password': 'newpassword123',
        }
        response = self.client.post('/api/users/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_duplicate_email(self):
        data = {
            'username': 'brandnew',
            'email': self.user.email,
            'password': 'newpassword123',
        }
        response = self.client.post('/api/users/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_profile_unauthenticated(self):
        response = self.client.get(PROFILE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(PROFILE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'existinguser')
        self.assertIn('stats', response.data)
        self.assertIn('achievements', response.data)

    def test_update_profile_success(self):
        self.client.force_authenticate(user=self.user)
        data = {'bio': 'Updated bio', 'display_name': 'Updated Name'}
        response = self.client.put(PROFILE_URL, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Updated bio')
        self.assertEqual(self.user.display_name, 'Updated Name')

    def test_patch_profile_success(self):
        self.client.force_authenticate(user=self.user)
        data = {'bio': 'Patched bio'}
        response = self.client.patch(PROFILE_URL, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Patched bio')

    def test_email_is_read_only_on_profile(self):
        self.client.force_authenticate(user=self.user)
        original_email = self.user.email
        response = self.client.put(PROFILE_URL, {'email': 'hacked@evil.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, original_email)

    def test_username_is_read_only_on_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(PROFILE_URL, {'username': 'hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'existinguser')
