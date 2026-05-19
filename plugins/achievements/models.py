from django.db import models
from django.conf import settings

class Achievement(models.Model):
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=500)
    icon = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='users'
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.username} earned {self.achievement.name}"
