from django.db import models
from django.conf import settings
import uuid
import random
import string

def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='created_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=255)
    is_public = models.BooleanField(default=True)
    invite_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        db_index=True,
    )

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = generate_invite_code()
            while Room.objects.filter(invite_code=self.invite_code).exists():
                self.invite_code = generate_invite_code()
        super().save(*args, **kwargs)


class RoomMember(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')