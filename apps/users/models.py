from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    is_pro = models.BooleanField(default=False)
    display_name = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.username