import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Movie, RoomVideo
from tests.helpers import create_test_user, response_list


class MovieModelTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='movieowner')

    def test_movie_creation_file(self):
        movie = Movie.objects.create(title='My Test Movie', description='Test Desc', video_type='FILE', owner=self.user)
        self.assertEqual(movie.title, 'My Test Movie')
        self.assertEqual(movie.video_type, 'FILE')
        self.assertEqual(str(movie), 'My Test Movie')

    def test_movie_creation_youtube(self):
        movie = Movie.objects.create(
            title='YouTube Movie',
            youtube_url='https://youtube.com/watch?v=123',
            video_type='YOUTUBE',
            owner=self.user,
        )
        self.assertEqual(movie.youtube_url, 'https://youtube.com/watch?v=123')

    def test_movie_default_video_type(self):
        movie = Movie.objects.create(title='Default', owner=self.user)
        self.assertEqual(movie.video_type, 'FILE')

    def test_movie_has_created_at(self):
        movie = Movie.objects.create(title='Dated', owner=self.user)
        self.assertIsNotNone(movie.created_at)


class RoomVideoModelTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='rvowner')
        self.movie = Movie.objects.create(title='Test Movie', owner=self.user)

    def test_room_video_creation(self):
        room_id = uuid.uuid4()
        rv = RoomVideo.objects.create(
            room_id=room_id, movie=self.movie, creator_name='Test Creator',
            room_name='Test Room', invite_code='TEST12', is_public=True,
        )
        self.assertEqual(rv.room_id, room_id)
        self.assertTrue(str(room_id) in str(rv))


class MoviesViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = create_test_user(username='user1')
        self.user2 = create_test_user(username='user2')
        self.movie1 = Movie.objects.create(title='Movie 1', owner=self.user1)
        self.room_id = uuid.uuid4()
        RoomVideo.objects.create(room_id=self.room_id, movie=self.movie1, is_public=True)

    def test_list_movies_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/movies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_list(response.data)), 1)

    def test_list_movies_only_own_movies(self):
        Movie.objects.create(title='Other Movie', owner=self.user2)
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/movies/')
        titles = [m['title'] for m in response_list(response.data)]
        self.assertEqual(titles, ['Movie 1'])

    def test_list_movies_unauthenticated(self):
        response = self.client.get('/api/movies/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_movie_youtube(self):
        self.client.force_authenticate(user=self.user1)
        data = {'title': 'New YouTube', 'video_type': 'YOUTUBE', 'youtube_url': 'https://youtube.com/watch?v=456'}
        response = self.client.post('/api/movies/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Movie.objects.count(), 2)

    def test_create_movie_file_without_file(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/movies/', {'title': 'Bad File', 'video_type': 'FILE'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_movie_youtube_without_url(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/movies/', {'title': 'Bad YT', 'video_type': 'YOUTUBE'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_room_movie_detail(self):
        response = self.client.get(f'/api/movies/room/{self.room_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['room_id']), str(self.room_id))
        self.assertEqual(response.data['movie']['title'], 'Movie 1')

    def test_get_room_movie_detail_not_found(self):
        response = self.client.get(f'/api/movies/room/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_active_rooms_with_movies(self):
        response = self.client.get('/api/movies/active-rooms/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response_list(response.data)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['movie_details']['title'], 'Movie 1')

    def test_active_rooms_excludes_private(self):
        RoomVideo.objects.create(
            room_id=uuid.uuid4(),
            movie=self.movie1,
            is_public=False,
        )
        response = self.client.get('/api/movies/active-rooms/')
        self.assertEqual(len(response_list(response.data)), 1)
