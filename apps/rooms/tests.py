import uuid
from django.test import TestCase
from django.db import IntegrityError
from rest_framework.test import APIClient
from rest_framework import status
from .models import Room, RoomMember, generate_invite_code
from tests.helpers import create_test_user, response_list


class RoomModelTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='roomcreator')

    def test_room_creation(self):
        room = Room.objects.create(creator=self.user, name='Test Room')
        self.assertEqual(room.name, 'Test Room')
        self.assertTrue(room.is_active)
        self.assertTrue(room.is_public)
        self.assertIsNotNone(room.invite_code)
        self.assertEqual(len(room.invite_code), 6)

    def test_room_member_creation(self):
        room = Room.objects.create(creator=self.user, name='Test Room')
        member = RoomMember.objects.create(room=room, user=self.user)
        self.assertEqual(member.room, room)
        self.assertEqual(member.user, self.user)

    def test_generate_invite_code_length(self):
        code = generate_invite_code()
        self.assertEqual(len(code), 6)

    def test_room_member_unique_together(self):
        room = Room.objects.create(creator=self.user, name='Dup Room')
        RoomMember.objects.create(room=room, user=self.user)
        with self.assertRaises(IntegrityError):
            RoomMember.objects.create(room=room, user=self.user)

    def test_private_room_not_in_public_queryset(self):
        Room.objects.create(creator=self.user, name='Private', is_public=False)
        public = Room.objects.filter(is_active=True, is_public=True)
        self.assertEqual(public.count(), 0)

    def test_inactive_room_excluded_from_active(self):
        Room.objects.create(creator=self.user, name='Inactive', is_active=False)
        active = Room.objects.filter(is_active=True)
        self.assertEqual(active.count(), 0)


class RoomViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = create_test_user(username='user1')
        self.user2 = create_test_user(username='user2')
        self.room = Room.objects.create(creator=self.user1, name='User1 Room')
        RoomMember.objects.create(room=self.room, user=self.user1)

    def test_create_room_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/rooms/', {'name': 'New API Room', 'is_public': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New API Room')
        self.assertEqual(Room.objects.count(), 2)

    def test_create_room_unauthenticated(self):
        response = self.client.post('/api/rooms/', {'name': 'Anonymous Room'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_room_adds_creator_as_member(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post('/api/rooms/', {'name': 'Member Room'}, format='json')
        new_room = Room.objects.get(name='Member Room')
        self.assertTrue(RoomMember.objects.filter(room=new_room, user=self.user1).exists())

    def test_create_private_room(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/rooms/', {'name': 'Private Room', 'is_public': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_public'])

    def test_list_rooms_public(self):
        response = self.client.get('/api/rooms/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_list(response.data)), 1)

    def test_list_rooms_excludes_private(self):
        Room.objects.create(creator=self.user1, name='Hidden', is_public=False)
        response = self.client.get('/api/rooms/')
        names = [r['name'] for r in response_list(response.data)]
        self.assertNotIn('Hidden', names)

    def test_join_room_by_id(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f'/api/rooms/{self.room.id}/join/')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(RoomMember.objects.filter(room=self.room, user=self.user2).exists())

    def test_rejoin_room_returns_200(self):
        RoomMember.objects.create(room=self.room, user=self.user2)
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f'/api/rooms/{self.room.id}/join/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_join_room_by_invalid_id(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f'/api/rooms/{uuid.uuid4()}/join/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_join_inactive_room_not_found(self):
        self.room.is_active = False
        self.room.save()
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f'/api/rooms/{self.room.id}/join/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_join_room_by_code(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/api/rooms/join-by-code/', {'invite_code': self.room.invite_code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(RoomMember.objects.filter(room=self.room, user=self.user2).exists())

    def test_join_room_by_code_case_insensitive(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/api/rooms/join-by-code/', {'invite_code': self.room.invite_code.lower()}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_join_room_by_invalid_code(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/api/rooms/join-by-code/', {'invite_code': 'INVALID1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_join_room_by_empty_code(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/api/rooms/join-by-code/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_rooms_list(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/rooms/my/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_list(response.data)), 1)
        self.assertEqual(response_list(response.data)[0]['name'], 'User1 Room')

    def test_room_detail_view(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/rooms/{self.room.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'User1 Room')

    def test_room_detail_unauthenticated(self):
        response = self.client.get(f'/api/rooms/{self.room.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
