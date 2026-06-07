import uuid
from django.test import TestCase
from apps.rooms.models import Room
from apps.rooms.signals import room_created_signal
from plugins.sync.models import RoomPlaybackState
from .models import Movie, RoomVideo
from .signals import _movie_id_from_payload, attach_video_to_room
from tests.helpers import create_test_user


class MovieIdPayloadTests(TestCase):
    def test_movie_id_snake_case(self):
        self.assertEqual(_movie_id_from_payload({'movie_id': 'abc'}), 'abc')

    def test_movie_id_camel_case(self):
        self.assertEqual(_movie_id_from_payload({'movieId': 'xyz'}), 'xyz')

    def test_empty_payload_returns_none(self):
        self.assertIsNone(_movie_id_from_payload(None))
        self.assertIsNone(_movie_id_from_payload({}))


class AttachVideoToRoomTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='signalowner')
        self.movie = Movie.objects.create(title='Attach Me', owner=self.user)

    def _send(self, room, raw_data):
        room_created_signal.send(
            sender=Room,
            room_id=room.id,
            room_name=room.name,
            creator_name=self.user.username,
            invite_code=room.invite_code,
            is_public=room.is_public,
            raw_data=raw_data,
        )

    def test_attach_existing_movie_by_id(self):
        room = Room.objects.create(creator=self.user, name='With Movie')
        self._send(room, {'movie_id': str(self.movie.id)})
        rv = RoomVideo.objects.get(room_id=room.id)
        self.assertEqual(rv.movie, self.movie)

    def test_attach_existing_movie_by_movieId(self):
        room = Room.objects.create(creator=self.user, name='Camel')
        self._send(room, {'movieId': str(self.movie.id)})
        self.assertTrue(RoomVideo.objects.filter(room_id=room.id).exists())

    def test_empty_raw_data_no_room_video(self):
        room = Room.objects.create(creator=self.user, name='Empty')
        self._send(room, None)
        self.assertFalse(RoomVideo.objects.filter(room_id=room.id).exists())

    def test_missing_movie_id_no_room_video(self):
        room = Room.objects.create(creator=self.user, name='No Id')
        self._send(room, {'video_type': 'FILE'})
        self.assertFalse(RoomVideo.objects.filter(room_id=room.id).exists())

    def test_invalid_movie_id_no_room_video(self):
        room = Room.objects.create(creator=self.user, name='Bad Id')
        self._send(room, {'movie_id': str(uuid.uuid4())})
        self.assertFalse(RoomVideo.objects.filter(room_id=room.id).exists())

    def test_youtube_creates_movie_and_attaches(self):
        room = Room.objects.create(creator=self.user, name='YT Room')
        self._send(room, {
            'video_type': 'YOUTUBE',
            'youtube_url': 'https://youtube.com/watch?v=test',
            'movie_title': 'Custom Title',
        })
        rv = RoomVideo.objects.get(room_id=room.id)
        self.assertEqual(rv.movie.video_type, 'YOUTUBE')
        self.assertEqual(rv.movie.title, 'Custom Title')

    def test_youtube_without_url_skipped(self):
        room = Room.objects.create(creator=self.user, name='No URL')
        self._send(room, {'video_type': 'YOUTUBE'})
        self.assertFalse(RoomVideo.objects.filter(room_id=room.id).exists())

    def test_attach_resets_playback_state(self):
        room = Room.objects.create(creator=self.user, name='Reset')
        RoomPlaybackState.objects.create(room_id=room.id, current_time=99, is_playing=True)
        self._send(room, {'movie_id': str(self.movie.id)})
        state = RoomPlaybackState.objects.get(room_id=room.id)
        self.assertEqual(state.current_time, 0.0)
        self.assertFalse(state.is_playing)

    def test_direct_call_attach_video(self):
        room = Room.objects.create(creator=self.user, name='Direct')
        attach_video_to_room(
            sender=None,
            room_id=room.id,
            creator_name=self.user.username,
            room_name=room.name,
            invite_code=room.invite_code,
            is_public=True,
            raw_data={'movie_id': str(self.movie.id)},
        )
        self.assertTrue(RoomVideo.objects.filter(room_id=room.id).exists())
