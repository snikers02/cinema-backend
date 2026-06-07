import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import ChatMessage
from tests.helpers import create_test_user


class ChatModelsTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='chatuser')
        self.room_id = uuid.uuid4()

    def test_chat_message_creation(self):
        msg = ChatMessage.objects.create(room_id=self.room_id, user=self.user, text='Hello world')
        self.assertEqual(msg.text, 'Hello world')
        self.assertEqual(msg.user, self.user)

    def test_chat_message_ordering(self):
        for i in range(3):
            ChatMessage.objects.create(room_id=self.room_id, user=self.user, text=f'Msg {i}')
        messages = list(ChatMessage.objects.filter(room_id=self.room_id))
        self.assertEqual(messages[0].text, 'Msg 0')


class ChatViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(username='chatuser')
        self.other_room = uuid.uuid4()
        self.room_id = uuid.uuid4()
        for i in range(5):
            ChatMessage.objects.create(room_id=self.room_id, user=self.user, text=f'Message {i}')

    def test_get_chat_history_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/chat/history/{self.room_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_get_chat_history_unauthenticated(self):
        response = self.client.get(f'/api/chat/history/{self.room_id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_chat_history_empty(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/chat/history/{self.other_room}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_get_chat_history_only_room_messages(self):
        ChatMessage.objects.create(room_id=self.other_room, user=self.user, text='Other room')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/chat/history/{self.room_id}/')
        texts = [m['text'] for m in response.data]
        self.assertNotIn('Other room', texts)

    def test_get_chat_history_limit_50(self):
        for i in range(60):
            ChatMessage.objects.create(room_id=self.room_id, user=self.user, text=f'Bulk {i}')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/chat/history/{self.room_id}/')
        self.assertLessEqual(len(response.data), 50)

    def test_chat_serializer_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/chat/history/{self.room_id}/')
        item = response.data[0]
        for field in ('id', 'username', 'text', 'created_at'):
            self.assertIn(field, item)
