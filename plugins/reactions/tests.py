import uuid
from django.test import TestCase
from django.db import IntegrityError
from .models import ReactionStat


class ReactionModelsTests(TestCase):
    def test_reaction_stat_creation(self):
        room_id = uuid.uuid4()
        stat = ReactionStat.objects.create(room_id=room_id, emoji='👍', count=5)
        self.assertEqual(stat.count, 5)

    def test_reaction_stat_default_count(self):
        room_id = uuid.uuid4()
        stat = ReactionStat.objects.create(room_id=room_id, emoji='🔥')
        self.assertEqual(stat.count, 0)

    def test_reaction_stat_unique_together(self):
        room_id = uuid.uuid4()
        ReactionStat.objects.create(room_id=room_id, emoji='👍')
        with self.assertRaises(IntegrityError):
            ReactionStat.objects.create(room_id=room_id, emoji='👍')
