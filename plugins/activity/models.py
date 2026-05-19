from django.db import models
from django.conf import settings

class ViewingHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='viewing_history'
    )
    movie = models.ForeignKey(
        'movies.Movie',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='views'
    )
    room_id = models.UUIDField(blank=True, null=True)
    watched_seconds = models.IntegerField(default=0)
    watched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        movie_title = self.movie.title if self.movie else "Unknown Movie"
        return f"{self.user.username} watched {movie_title} for {self.watched_seconds}s"
