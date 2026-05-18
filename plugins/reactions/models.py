from django.db import models

class ReactionStat(models.Model):
    room_id = models.UUIDField()
    emoji = models.CharField(max_length=10)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('room_id', 'emoji')