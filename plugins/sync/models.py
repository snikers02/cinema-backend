from django.db import models

class RoomPlaybackState(models.Model):
    room_id = models.UUIDField(unique=True)
    
    current_time = models.FloatField(default=0.0)
    is_playing = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State of {self.room_id}"