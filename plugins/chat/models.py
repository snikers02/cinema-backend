from django.db import models
from django.conf import settings

class ChatMessage(models.Model):
    # UUID кімнати з Ядра
    room_id = models.UUIDField(db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']