from django.db import models


class RoomPlaybackState(models.Model):
    id = models.BigAutoField(primary_key=True, serialize=False)

    room_id = models.UUIDField(unique=True)
    
    current_time = models.FloatField(default=0.0)
    is_playing = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State of {self.room_id}"


class RoomPlaybackRules(models.Model):
    id = models.BigAutoField(primary_key=True, serialize=False)
    room_id = models.UUIDField(unique=True)
    anyone_can_control = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rules for room {self.room_id} (anyone: {self.anyone_can_control})"


class RoomAuthorizedController(models.Model):
    id = models.BigAutoField(primary_key=True, serialize=False)
    room_id = models.UUIDField()
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='authorized_room_controls'
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room_id', 'user')

    def __str__(self):
        return f"User {self.user.username} authorized for room {self.room_id}"


def check_user_can_control_playback(user, room_id):
    if not user or not user.is_authenticated:
        return False

    from apps.rooms.models import Room  # type: ignore
    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        return False

    if room.creator == user:
        return True

    rules, _ = RoomPlaybackRules.objects.get_or_create(
        room_id=room_id,
        defaults={'anyone_can_control': False}
    )
    if rules.anyone_can_control:
        return True

    return RoomAuthorizedController.objects.filter(room_id=room_id, user=user).exists()