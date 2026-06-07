from django.test import TestCase
from .models import Room, RoomMember
from .serializers import RoomSerializer, RoomMemberSerializer
from tests.helpers import create_test_user


class RoomSerializerTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='serializeruser')

    def test_members_count_zero_for_new_room(self):
        room = Room(creator=self.user, name='Unsaved')
        data = RoomSerializer(room).data
        self.assertEqual(data['members_count'], 0)

    def test_members_count_reflects_members(self):
        room = Room.objects.create(creator=self.user, name='Counted')
        RoomMember.objects.create(room=room, user=self.user)
        friend = create_test_user(username='member2')
        RoomMember.objects.create(room=room, user=friend)
        data = RoomSerializer(room).data
        self.assertEqual(data['members_count'], 2)

    def test_creator_name_read_only(self):
        room = Room.objects.create(creator=self.user, name='Named')
        data = RoomSerializer(room).data
        self.assertEqual(data['creator_name'], 'serializeruser')

    def test_invite_code_in_serialized_data(self):
        room = Room.objects.create(creator=self.user, name='Coded')
        data = RoomSerializer(room).data
        self.assertEqual(len(data['invite_code']), 6)


class RoomMemberSerializerTests(TestCase):
    def test_serializes_username(self):
        user = create_test_user(username='memberuser')
        room = Room.objects.create(creator=user, name='R')
        member = RoomMember.objects.create(room=room, user=user)
        data = RoomMemberSerializer(member).data
        self.assertEqual(data['username'], 'memberuser')
