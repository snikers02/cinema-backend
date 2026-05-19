import uuid
from django.db import models
from django.conf import settings

class Movie(models.Model):
    VIDEO_TYPES = [
        ('FILE', 'Local File'),
        ('YOUTUBE', 'YouTube Video'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_type = models.CharField(
        max_length=20,
        choices=VIDEO_TYPES,
        default='FILE'
    )
    
    video_file = models.FileField(upload_to='movies/videos/', blank=True, null=True)
    youtube_url = models.URLField(max_length=500, blank=True, null=True)
    poster = models.ImageField(upload_to='movies/posters/', blank=True, null=True)
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_movies'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title




class RoomVideo(models.Model):
    room_id = models.UUIDField(unique=True) # ID з Ядра
    creator_name = models.CharField(max_length=255, blank=True, null=True)
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    room_name = models.CharField(max_length=255, blank=True, null=True)
    invite_code = models.CharField(max_length=10, blank=True, null=True)
    is_public = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Video for room {self.room_id}"