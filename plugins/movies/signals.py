from django.dispatch import receiver

from apps.rooms.signals import room_created_signal
from .models import Movie, RoomVideo


def _movie_id_from_payload(raw_data):
    if not raw_data:
        return None
    return raw_data.get("movie_id") or raw_data.get("movieId")


@receiver(room_created_signal)
def attach_video_to_room(sender, room_id, creator_name, room_name, raw_data, **kwargs):
    movie_id = _movie_id_from_payload(raw_data)

    if not movie_id:
        return

    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return

    RoomVideo.objects.update_or_create(
        room_id=room_id,
        defaults={"movie": movie, "creator_name": creator_name, "room_name": room_name},
    )