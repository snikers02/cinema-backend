from django.dispatch import receiver

from apps.rooms.signals import room_created_signal  # type: ignore
from .models import Movie, RoomVideo


def _movie_id_from_payload(raw_data):
    if not raw_data:
        return None
    return raw_data.get("movie_id") or raw_data.get("movieId")


@receiver(room_created_signal)
def attach_video_to_room(sender, room_id, creator_name, room_name, invite_code, is_public, raw_data, **kwargs):
    print(f"!!! attach_video_to_room signal triggered with raw_data={raw_data}")
    if not raw_data:
        print("!!! attach_video_to_room: raw_data is empty, returning")
        return

    video_type = raw_data.get("video_type", "FILE")
    print(f"!!! attach_video_to_room: video_type={video_type}")

    if video_type == "YOUTUBE":
        youtube_url = raw_data.get("youtube_url")
        print(f"!!! attach_video_to_room: youtube_url={youtube_url}")
        if not youtube_url:
            print("!!! attach_video_to_room: youtube_url is empty, returning")
            return
        
        from apps.rooms.models import Room  # type: ignore
        try:
            room = Room.objects.get(id=room_id)
            owner = room.creator
            print(f"!!! attach_video_to_room: found room owner={owner}")
        except Exception as e:
            print(f"!!! attach_video_to_room: failed to get Room with id={room_id}: {e}")
            return

        movie_title = raw_data.get("movie_title") or f"YouTube: {room_name}"
        movie = Movie.objects.create(
            title=movie_title,
            video_type="YOUTUBE",
            youtube_url=youtube_url,
            owner=owner
        )
    else:
        movie_id = _movie_id_from_payload(raw_data)
        if not movie_id:
            return

        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            return

    RoomVideo.objects.update_or_create(
        room_id=room_id,
        defaults={
            "movie": movie,
            "creator_name": creator_name,
            "room_name": room_name,
            "invite_code": invite_code,
            "is_public": is_public
        },
    )

    # Також скидаємо поточний стан відтворення в нуль при встановленні/зміні фільму у кімнаті
    try:
        from plugins.sync.models import RoomPlaybackState
        RoomPlaybackState.objects.update_or_create(
            room_id=room_id,
            defaults={
                "current_time": 0.0,
                "is_playing": False
            }
        )
        print(f"!!! Reset RoomPlaybackState for room {room_id} because movie was updated/attached !!!")
    except ImportError:
        pass