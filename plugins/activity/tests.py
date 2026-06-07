import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from plugins.movies.models import Movie
from plugins.achievements.models import UserAchievement
from .models import ViewingHistory
from tests.helpers import create_test_user


class ActivityModelsTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='activityuser')
        self.movie = Movie.objects.create(title='Activity Movie', owner=self.user)

    def test_viewing_history_creation(self):
        vh = ViewingHistory.objects.create(user=self.user, movie=self.movie, watched_seconds=120)
        self.assertEqual(vh.watched_seconds, 120)
        self.assertTrue('activityuser' in str(vh))

    def test_viewing_history_creation_no_movie(self):
        vh = ViewingHistory.objects.create(user=self.user, watched_seconds=60)
        self.assertIsNone(vh.movie)
        self.assertTrue('Unknown Movie' in str(vh))

    def test_viewing_history_watched_at_auto_set(self):
        vh = ViewingHistory.objects.create(user=self.user, movie=self.movie, watched_seconds=10)
        self.assertIsNotNone(vh.watched_at)


class ActivityViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(username='activityuser')
        self.movie = Movie.objects.create(title='Activity Movie', owner=self.user)
        self.room_id = str(uuid.uuid4())

    def test_record_activity_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/activity/record/', {
            'movie_id': self.movie.id,
            'room_id': self.room_id,
            'seconds': 300,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['watched_count'], 1)

    def test_record_activity_default_seconds(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/activity/record/', {'movie_id': self.movie.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vh = ViewingHistory.objects.get(user=self.user)
        self.assertEqual(vh.watched_seconds, 0)

    def test_record_activity_multiple_increments_count(self):
        self.client.force_authenticate(user=self.user)
        for _ in range(3):
            self.client.post('/api/activity/record/', {'movie_id': self.movie.id, 'seconds': 10}, format='json')
        self.assertEqual(ViewingHistory.objects.filter(user=self.user).count(), 3)

    def test_record_activity_triggers_achievement(self):
        self.client.force_authenticate(user=self.user)
        self.client.post('/api/activity/record/', {'movie_id': self.movie.id, 'seconds': 100}, format='json')
        self.assertTrue(UserAchievement.objects.filter(user=self.user, achievement__key='movie_buff').exists())

    def test_record_activity_missing_movie(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/activity/record/', {'room_id': self.room_id, 'seconds': 300}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_record_activity_invalid_movie(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/activity/record/', {'movie_id': uuid.uuid4(), 'seconds': 300}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_record_activity_unauthenticated(self):
        response = self.client.post('/api/activity/record/', {'movie_id': self.movie.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_record_activity_without_room_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/activity/record/', {'movie_id': self.movie.id, 'seconds': 50}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vh = ViewingHistory.objects.get(user=self.user)
        self.assertIsNone(vh.room_id)
