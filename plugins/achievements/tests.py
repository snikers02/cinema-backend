from django.test import TestCase
from django.db import IntegrityError
from apps.rooms.models import Room
from plugins.social.models import Friendship
from plugins.activity.models import ViewingHistory
from plugins.movies.models import Movie
from plugins.social.views import friend_added_signal
from plugins.activity.views import movie_watched_signal
from .models import Achievement, UserAchievement
from .signals import grant_achievement, handle_room_created
from tests.helpers import create_test_user


class AchievementsModelsTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='achiever')
        self.achievement = Achievement.objects.create(
            name='Test Achievement', key='test_key', description='Test Desc',
        )

    def test_achievement_creation(self):
        self.assertEqual(str(self.achievement), 'Test Achievement')

    def test_user_achievement_creation(self):
        ua = UserAchievement.objects.create(user=self.user, achievement=self.achievement)
        self.assertTrue('earned Test Achievement' in str(ua))

    def test_user_achievement_unique_together(self):
        UserAchievement.objects.create(user=self.user, achievement=self.achievement)
        with self.assertRaises(IntegrityError):
            UserAchievement.objects.create(user=self.user, achievement=self.achievement)


class AchievementsSignalsTests(TestCase):
    def setUp(self):
        self.user1 = create_test_user(username='achiever1')
        self.user2 = create_test_user(username='achiever2')

    def test_grant_achievement_new(self):
        grant_achievement(self.user1, 'first_room')
        self.assertTrue(UserAchievement.objects.filter(user=self.user1, achievement__key='first_room').exists())

    def test_grant_achievement_existing_key(self):
        ach = Achievement.objects.create(name='Existing', key='existing_key', description='Desc')
        grant_achievement(self.user1, 'existing_key')
        self.assertTrue(UserAchievement.objects.filter(user=self.user1, achievement=ach).exists())

    def test_grant_achievement_unknown_key_noop(self):
        before = UserAchievement.objects.count()
        grant_achievement(self.user1, 'nonexistent_key_xyz')
        self.assertEqual(UserAchievement.objects.count(), before)

    def test_grant_achievement_idempotent(self):
        grant_achievement(self.user1, 'first_friend')
        grant_achievement(self.user1, 'first_friend')
        count = UserAchievement.objects.filter(user=self.user1, achievement__key='first_friend').count()
        self.assertEqual(count, 1)

    def test_room_created_signal(self):
        Room.objects.create(creator=self.user1, name='My Room')
        self.assertTrue(UserAchievement.objects.filter(user=self.user1, achievement__key='first_room').exists())

    def test_room_update_does_not_regrant(self):
        room = Room.objects.create(creator=self.user1, name='Update Room')
        count = UserAchievement.objects.filter(user=self.user1, achievement__key='first_room').count()
        room.name = 'Renamed'
        room.save()
        self.assertEqual(
            UserAchievement.objects.filter(user=self.user1, achievement__key='first_room').count(),
            count,
        )

    def test_friend_added_signal(self):
        if friend_added_signal:
            friend_added_signal.send(sender=None, user=self.user1, friend=self.user2)
            self.assertTrue(UserAchievement.objects.filter(user=self.user1, achievement__key='first_friend').exists())
            self.assertTrue(UserAchievement.objects.filter(user=self.user2, achievement__key='first_friend').exists())

    def test_friend_50_achievement(self):
        if friend_added_signal:
            for i in range(49):
                f = create_test_user(username=f'f{i}')
                Friendship.objects.create(user=self.user1, friend=f, status='ACCEPTED')
            last = create_test_user(username='f_last')
            Friendship.objects.create(user=self.user1, friend=last, status='ACCEPTED')
            friend_added_signal.send(sender=None, user=self.user1, friend=last)
            self.assertTrue(UserAchievement.objects.filter(user=self.user1, achievement__key='friend_50').exists())

    def test_movie_watched_signal(self):
        if movie_watched_signal:
            movie_watched_signal.send(sender=None, user=self.user1, movie=None, seconds=100)
            self.assertTrue(UserAchievement.objects.filter(user=self.user1, achievement__key='movie_buff').exists())

    def test_movies_100_achievement(self):
        if movie_watched_signal:
            movie = Movie.objects.create(title='M', owner=self.user1)
            for _ in range(100):
                ViewingHistory.objects.create(user=self.user1, movie=movie, watched_seconds=1)
            movie_watched_signal.send(sender=None, user=self.user1, movie=movie, seconds=1)
            self.assertTrue(UserAchievement.objects.filter(user=self.user1, achievement__key='movies_100').exists())
