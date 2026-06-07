import uuid
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from apps.rooms.signals import socket_message_signal
from plugins.chat.models import ChatMessage
import plugins.signals  # noqa: F401 — register handler
from tests.helpers import create_test_user


class ChatSignalTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='chatsignal')
        self.room_id = uuid.uuid4()

    def _send(self, user, text):
        socket_message_signal.send(
            sender=None,
            room_id=self.room_id,
            user=user,
            message_type='chat.message',
            data={'text': text},
        )

    def test_chat_message_saved(self):
        self._send(self.user, 'Saved message')
        self.assertTrue(ChatMessage.objects.filter(room_id=self.room_id, text='Saved message').exists())

    def test_empty_text_not_saved(self):
        self._send(self.user, '')
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_anonymous_user_not_saved(self):
        self._send(AnonymousUser(), 'Anon msg')
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_non_chat_type_ignored(self):
        socket_message_signal.send(
            sender=None,
            room_id=self.room_id,
            user=self.user,
            message_type='play',
            data={'text': 'Should not save'},
        )
        self.assertEqual(ChatMessage.objects.count(), 0)
