from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Movie, RoomVideo
from .serializers import MoviesSerializer, RoomWithMovieSerializer
from tests.helpers import create_test_user
import uuid


class MoviesSerializerTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='sermovie')

    def test_youtube_valid(self):
        s = MoviesSerializer(data={
            'title': 'YT', 'video_type': 'YOUTUBE', 'youtube_url': 'https://youtube.com/watch?v=abc',
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_youtube_missing_url(self):
        s = MoviesSerializer(data={'title': 'YT', 'video_type': 'YOUTUBE'})
        self.assertFalse(s.is_valid())
        self.assertIn('youtube_url', s.errors)

    def test_youtube_invalid_domain(self):
        s = MoviesSerializer(data={
            'title': 'YT', 'video_type': 'YOUTUBE', 'youtube_url': 'https://example.com/video',
        })
        self.assertFalse(s.is_valid())

    def test_file_missing_on_create(self):
        s = MoviesSerializer(data={'title': 'File', 'video_type': 'FILE'})
        self.assertFalse(s.is_valid())

    def test_file_unsupported_extension(self):
        bad = SimpleUploadedFile('clip.txt', b'content', content_type='text/plain')
        s = MoviesSerializer(data={'title': 'Bad', 'video_type': 'FILE', 'video_file': bad})
        self.assertFalse(s.is_valid())

    def test_file_valid_mp4(self):
        mp4 = SimpleUploadedFile('clip.mp4', b'fake', content_type='video/mp4')
        s = MoviesSerializer(data={'title': 'Good', 'video_type': 'FILE', 'video_file': mp4})
        self.assertTrue(s.is_valid(), s.errors)

    def test_file_update_without_reupload(self):
        movie = Movie.objects.create(title='Existing', video_type='FILE', owner=self.user)
        s = MoviesSerializer(instance=movie, data={'title': 'Renamed', 'video_type': 'FILE'}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)

    def test_youtube_clears_video_file(self):
        s = MoviesSerializer(data={
            'title': 'YT', 'video_type': 'YOUTUBE', 'youtube_url': 'https://youtu.be/abc',
        })
        self.assertTrue(s.is_valid())
        self.assertIsNone(s.validated_data.get('video_file'))


class RoomWithMovieSerializerTests(TestCase):
    def test_nested_movie_details(self):
        user = create_test_user(username='nested')
        movie = Movie.objects.create(title='Nested Movie', owner=user)
        rv = RoomVideo.objects.create(room_id=uuid.uuid4(), movie=movie, room_name='R')
        data = RoomWithMovieSerializer(rv).data
        self.assertEqual(data['movie_details']['title'], 'Nested Movie')
        self.assertIn('room_id', data)
