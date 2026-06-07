from django.test import TestCase
from django.db import IntegrityError
from rest_framework.test import APIClient
from rest_framework import status
from .models import Friendship
from tests.helpers import create_test_user


class SocialModelsTests(TestCase):
    def setUp(self):
        self.user1 = create_test_user(username='social1')
        self.user2 = create_test_user(username='social2')

    def test_friendship_creation(self):
        fs = Friendship.objects.create(user=self.user1, friend=self.user2, status='PENDING')
        self.assertEqual(fs.status, 'PENDING')
        self.assertTrue('social1' in str(fs) and 'social2' in str(fs))

    def test_friendship_unique_together(self):
        Friendship.objects.create(user=self.user1, friend=self.user2, status='PENDING')
        with self.assertRaises(IntegrityError):
            Friendship.objects.create(user=self.user1, friend=self.user2, status='PENDING')


class SocialViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = create_test_user(username='social1')
        self.user2 = create_test_user(username='social2')
        self.user3 = create_test_user(username='social3')

    def test_add_friend_by_id(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/add/', {'friend_id': self.user2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'PENDING')

    def test_add_friend_by_username(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/add/', {'username': 'social3'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_friend_self(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/add/', {'friend_id': self.user1.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_friend_missing_params(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/add/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_friend_invalid_user(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/add/', {'friend_id': 9999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_friend_already_friends(self):
        Friendship.objects.create(user=self.user1, friend=self.user2, status='ACCEPTED')
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/add/', {'friend_id': self.user2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Already friends')

    def test_add_friend_request_already_sent(self):
        Friendship.objects.create(user=self.user1, friend=self.user2, status='PENDING')
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/add/', {'friend_id': self.user2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Friend request already sent')

    def test_add_friend_accept_pending(self):
        Friendship.objects.create(user=self.user2, friend=self.user1, status='PENDING')
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/add/', {'friend_id': self.user2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ACCEPTED')

    def test_accept_friend(self):
        Friendship.objects.create(user=self.user2, friend=self.user1, status='PENDING')
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/accept/', {'user_id': self.user2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Friendship.objects.filter(user=self.user2, friend=self.user1, status='ACCEPTED').exists())

    def test_accept_friend_not_found(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/accept/', {'user_id': self.user2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_accept_friend_missing_user_id(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/accept/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_friend(self):
        Friendship.objects.create(user=self.user1, friend=self.user2, status='ACCEPTED')
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/remove/', {'friend_id': self.user2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Friendship.objects.filter(user=self.user1, friend=self.user2).exists())

    def test_remove_friend_not_found(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/remove/', {'friend_id': self.user2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_friend_missing_id(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/social/remove/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_friends_list(self):
        Friendship.objects.create(user=self.user1, friend=self.user2, status='ACCEPTED')
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/social/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'social2')

    def test_friends_list_includes_profile_fields(self):
        self.user2.display_name = 'Display Two'
        self.user2.is_pro = True
        self.user2.save()
        Friendship.objects.create(user=self.user1, friend=self.user2, status='ACCEPTED')
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/social/')
        self.assertEqual(response.data[0]['display_name'], 'Display Two')
        self.assertTrue(response.data[0]['is_pro'])

    def test_social_endpoints_require_auth(self):
        for url, method, data in [
            ('/api/social/', 'get', None),
            ('/api/social/add/', 'post', {'friend_id': 1}),
            ('/api/social/accept/', 'post', {'user_id': 1}),
            ('/api/social/remove/', 'post', {'friend_id': 1}),
        ]:
            response = getattr(self.client, method)(url, data or {}, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, url)
