import uuid
from django.test import TestCase
from apps.rooms.signals import socket_message_signal
from .models import ReactionStat
from tests.helpers import create_test_user


class ReactionSignalTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='reactionuser')
        self.room_id = uuid.uuid4()

    def _send(self, data):
        socket_message_signal.send(
            sender=None,
            room_id=self.room_id,
            user=self.user,
            message_type='reaction.send',
            data=data,
        )

    def test_reaction_creates_new_stat(self):
        self._send({'emoji': '👍'})
        stat = ReactionStat.objects.get(room_id=self.room_id, emoji='👍')
        self.assertEqual(stat.count, 1)

    def test_reaction_increments_existing_stat(self):
        ReactionStat.objects.create(room_id=self.room_id, emoji='🔥', count=3)
        self._send({'emoji': '🔥'})
        stat = ReactionStat.objects.get(room_id=self.room_id, emoji='🔥')
        self.assertEqual(stat.count, 4)

    def test_reaction_missing_emoji_noop(self):
        self._send({})
        self.assertEqual(ReactionStat.objects.count(), 0)

    def test_non_reaction_message_ignored(self):
        socket_message_signal.send(
            sender=None,
            room_id=self.room_id,
            user=self.user,
            message_type='chat.message',
            data={'emoji': '👍'},
        )
        self.assertEqual(ReactionStat.objects.count(), 0)

    def test_multiple_reactions_accumulate(self):
        self._send({'emoji': '❤️'})
        self._send({'emoji': '❤️'})
        stat = ReactionStat.objects.get(room_id=self.room_id, emoji='❤️')
        self.assertEqual(stat.count, 2)

    def test_different_emojis_separate_stats(self):
        self._send({'emoji': '👍'})
        self._send({'emoji': '🔥'})
        self.assertEqual(ReactionStat.objects.filter(room_id=self.room_id).count(), 2)
