from django.test import TestCase
from django.contrib.auth import get_user_model
from plugins.activity.models import ViewingHistory
from plugins.movies.models import Movie
from plugins.social.models import Friendship
from plugins.achievements.models import Achievement, UserAchievement
from apps.rooms.models import Room
from apps.users.serializers import RegisterSerializer, UserProfileSerializer
from tests.helpers import create_test_user

User = get_user_model()


class RegisterSerializerTests(TestCase):
    def test_valid_registration_data(self):
        serializer = RegisterSerializer(data={
            'username': 'newbie',
            'email': 'newbie@test.com',
            'password': 'strongpass123',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_user_via_serializer(self):
        serializer = RegisterSerializer(data={
            'username': 'created',
            'email': 'created@test.com',
            'password': 'strongpass123',
        })
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertTrue(User.objects.filter(username='created').exists())
        self.assertTrue(user.check_password('strongpass123'))

    def test_missing_username_invalid(self):
        serializer = RegisterSerializer(data={'email': 'a@b.com', 'password': 'x'})
        self.assertFalse(serializer.is_valid())

    def test_missing_email_invalid(self):
        serializer = RegisterSerializer(data={'username': 'u', 'password': 'x'})
        self.assertFalse(serializer.is_valid())


class UserProfileSerializerTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='profileuser', display_name='Profile')

    def test_stats_empty_user(self):
        data = UserProfileSerializer(self.user).data
        self.assertEqual(data['stats']['watched_count'], 0)
        self.assertEqual(data['stats']['friends_count'], 0)
        self.assertEqual(data['stats']['rooms_count'], 0)

    def test_stats_with_viewing_history(self):
        movie = Movie.objects.create(title='Stats Movie', owner=self.user)
        ViewingHistory.objects.create(user=self.user, movie=movie, watched_seconds=3600)
        ViewingHistory.objects.create(user=self.user, movie=movie, watched_seconds=1800)
        stats = UserProfileSerializer(self.user).data['stats']
        self.assertEqual(stats['watched_count'], 2)
        self.assertEqual(stats['watched_hours'], 1.5)

    def test_stats_with_friends(self):
        friend = create_test_user(username='friend1')
        Friendship.objects.create(user=self.user, friend=friend, status='ACCEPTED')
        stats = UserProfileSerializer(self.user).data['stats']
        self.assertEqual(stats['friends_count'], 1)

    def test_stats_with_rooms(self):
        Room.objects.create(creator=self.user, name='Room A')
        Room.objects.create(creator=self.user, name='Room B')
        stats = UserProfileSerializer(self.user).data['stats']
        self.assertEqual(stats['rooms_count'], 2)

    def test_recent_activity_returns_last_entries(self):
        movie = Movie.objects.create(title='Recent', owner=self.user)
        for i in range(12):
            ViewingHistory.objects.create(user=self.user, movie=movie, watched_seconds=i)
        activity = UserProfileSerializer(self.user).data['recent_activity']
        self.assertEqual(len(activity), 10)

    def test_recent_activity_movie_title(self):
        movie = Movie.objects.create(title='Named Movie', owner=self.user)
        ViewingHistory.objects.create(user=self.user, movie=movie, watched_seconds=10)
        activity = UserProfileSerializer(self.user).data['recent_activity']
        self.assertEqual(activity[0]['movie_title'], 'Named Movie')

    def test_recent_activity_unknown_movie(self):
        ViewingHistory.objects.create(user=self.user, watched_seconds=10)
        activity = UserProfileSerializer(self.user).data['recent_activity']
        self.assertEqual(activity[0]['movie_title'], 'Unknown Movie')

    def test_achievements_lists_all_keys(self):
        achs = UserProfileSerializer(self.user).data['achievements']
        keys = {a['key'] for a in achs}
        self.assertIn('first_room', keys)
        self.assertIn('movie_buff', keys)
        self.assertIn('friend_50', keys)

    def test_achievements_earned_flag(self):
        ach = Achievement.objects.create(name='Test', key='test_ach', description='d')
        UserAchievement.objects.create(user=self.user, achievement=ach)
        achs = UserProfileSerializer(self.user).data['achievements']
        earned = [a for a in achs if a['key'] == 'test_ach'][0]
        self.assertTrue(earned['earned'])
        self.assertIsNotNone(earned['earned_at'])

    def test_achievements_not_earned(self):
        Achievement.objects.create(name='Unearned', key='unearned_key', description='d')
        achs = UserProfileSerializer(self.user).data['achievements']
        item = [a for a in achs if a['key'] == 'unearned_key'][0]
        self.assertFalse(item['earned'])
        self.assertIsNone(item['earned_at'])
