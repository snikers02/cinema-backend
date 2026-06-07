import uuid
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIClient
from rest_framework import status
from apps.rooms.models import Room, RoomMember
from .models import (
    RoomPlaybackState, RoomPlaybackRules, RoomAuthorizedController,
    check_user_can_control_playback,
)
from unittest.mock import patch
from tests.helpers import create_test_user


class SyncModelsTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='syncuser')
        self.other = create_test_user(username='syncother')
        self.room = Room.objects.create(creator=self.user, name='Sync Room')

    def test_room_playback_state_creation(self):
        state = RoomPlaybackState.objects.create(room_id=self.room.id, current_time=10.5, is_playing=True)
        self.assertEqual(state.current_time, 10.5)
        self.assertTrue(state.is_playing)

    def test_room_playback_rules_creation(self):
        rules = RoomPlaybackRules.objects.create(room_id=self.room.id, anyone_can_control=True)
        self.assertTrue(rules.anyone_can_control)

    def test_room_authorized_controller_creation(self):
        controller = RoomAuthorizedController.objects.create(room_id=self.room.id, user=self.other)
        self.assertEqual(controller.user, self.other)

    def test_check_user_can_control_unauthenticated(self):
        self.assertFalse(check_user_can_control_playback(None, self.room.id))

    def test_check_user_can_control_anonymous(self):
        self.assertFalse(check_user_can_control_playback(AnonymousUser(), self.room.id))

    def test_check_user_can_control_room_not_exist(self):
        self.assertFalse(check_user_can_control_playback(self.user, uuid.uuid4()))

    def test_creator_can_always_control(self):
        self.assertTrue(check_user_can_control_playback(self.user, self.room.id))

    def test_anyone_can_control_rule(self):
        RoomPlaybackRules.objects.create(room_id=self.room.id, anyone_can_control=True)
        self.assertTrue(check_user_can_control_playback(self.other, self.room.id))

    def test_authorized_controller_can_control(self):
        RoomAuthorizedController.objects.create(room_id=self.room.id, user=self.other)
        self.assertTrue(check_user_can_control_playback(self.other, self.room.id))

    def test_non_member_cannot_control(self):
        self.assertFalse(check_user_can_control_playback(self.other, self.room.id))


class SyncViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.creator = create_test_user(username='creator')
        self.other_user = create_test_user(username='other')
        self.room = Room.objects.create(creator=self.creator, name='Sync Room')

    @patch('plugins.sync.views.async_to_sync')
    def test_get_room_rules(self, mock_async):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f'/api/sync/rules/{self.room.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['anyone_can_control'])
        self.assertFalse(response.data['can_control'])

    @patch('plugins.sync.views.async_to_sync')
    def test_get_room_rules_creator_can_control(self, mock_async):
        self.client.force_authenticate(user=self.creator)
        response = self.client.get(f'/api/sync/rules/{self.room.id}/')
        self.assertTrue(response.data['can_control'])

    @patch('plugins.sync.views.async_to_sync')
    def test_get_room_rules_not_found(self, mock_async):
        self.client.force_authenticate(user=self.creator)
        response = self.client.get(f'/api/sync/rules/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('plugins.sync.views.async_to_sync')
    def test_post_room_rules_by_creator(self, mock_async):
        self.client.force_authenticate(user=self.creator)
        response = self.client.post(
            f'/api/sync/rules/{self.room.id}/',
            {'anyone_can_control': True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['anyone_can_control'])
        self.assertTrue(response.data['can_control'])

    @patch('plugins.sync.views.async_to_sync')
    def test_post_room_rules_by_other_user(self, mock_async):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            f'/api/sync/rules/{self.room.id}/',
            {'anyone_can_control': True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('plugins.sync.views.async_to_sync')
    def test_grant_control_success(self, mock_async):
        self.client.force_authenticate(user=self.creator)
        response = self.client.post(
            f'/api/sync/rules/{self.room.id}/grant/',
            {'user_id': self.other_user.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            RoomAuthorizedController.objects.filter(room_id=self.room.id, user=self.other_user).exists()
        )

    @patch('plugins.sync.views.async_to_sync')
    def test_grant_control_by_username(self, mock_async):
        self.client.force_authenticate(user=self.creator)
        response = self.client.post(
            f'/api/sync/rules/{self.room.id}/grant/',
            {'username': 'other'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('plugins.sync.views.async_to_sync')
    def test_grant_control_owner_already_has_control(self, mock_async):
        self.client.force_authenticate(user=self.creator)
        response = self.client.post(
            f'/api/sync/rules/{self.room.id}/grant/',
            {'user_id': self.creator.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Owner already has control', response.data['message'])

    @patch('plugins.sync.views.async_to_sync')
    def test_grant_control_not_creator(self, mock_async):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(f'/api/sync/rules/{self.room.id}/grant/', {'user_id': self.creator.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('plugins.sync.views.async_to_sync')
    def test_grant_control_missing_data(self, mock_async):
        self.client.force_authenticate(user=self.creator)
        response = self.client.post(f'/api/sync/rules/{self.room.id}/grant/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('plugins.sync.views.async_to_sync')
    def test_grant_control_user_not_found(self, mock_async):
        self.client.force_authenticate(user=self.creator)
        response = self.client.post(f'/api/sync/rules/{self.room.id}/grant/', {'user_id': 99999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('plugins.sync.views.async_to_sync')
    def test_revoke_control_success(self, mock_async):
        RoomAuthorizedController.objects.create(room_id=self.room.id, user=self.other_user)
        self.client.force_authenticate(user=self.creator)
        response = self.client.post(
            f'/api/sync/rules/{self.room.id}/revoke/',
            {'user_id': self.other_user.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            RoomAuthorizedController.objects.filter(room_id=self.room.id, user=self.other_user).exists()
        )

    @patch('plugins.sync.views.async_to_sync')
    def test_revoke_control_not_creator(self, mock_async):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(f'/api/sync/rules/{self.room.id}/revoke/', {'user_id': self.creator.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('plugins.sync.views.async_to_sync')
    def test_revoke_control_missing_user_id(self, mock_async):
        self.client.force_authenticate(user=self.creator)
        response = self.client.post(f'/api/sync/rules/{self.room.id}/revoke/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
