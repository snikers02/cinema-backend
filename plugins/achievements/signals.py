from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.rooms.models import Room  # type: ignore
from .models import Achievement, UserAchievement

def grant_achievement(user, key):
    try:
        achievement = Achievement.objects.get(key=key)
        UserAchievement.objects.get_or_create(user=user, achievement=achievement)
    except Achievement.DoesNotExist:
        defaults = {
            "first_room": ("Перша кімната", "Ви створили свою першу кімнату для перегляду!", "crown"),
            "first_friend": ("Перший друг", "Додано першого друга до вашої кінокомпанії!", "heart"),
            "movie_buff": ("Кіноман", "Ви переглянули свій перший фільм!", "fire"),
            "streak_7": ("Сім днів", "Активність протягом 7 днів поспіль!", "streak_7"),
            "movies_100": ("Кіномарафон", "Ви переглянули 100 фільмів!", "movies_100"),
            "friend_50": ("Душа компанії", "У вас 50 друзів!", "friend_50"),
        }
        if key in defaults:
            name, desc, icon = defaults[key]
            achievement = Achievement.objects.create(name=name, key=key, description=desc, icon=icon)
            UserAchievement.objects.get_or_create(user=user, achievement=achievement)


@receiver(post_save, sender=Room)
def handle_room_created(sender, instance, created, **kwargs):
    if created and instance.creator:
        grant_achievement(instance.creator, 'first_room')


try:
    from plugins.social.views import friend_added_signal
except ImportError:
    friend_added_signal = None

if friend_added_signal:
    @receiver(friend_added_signal)
    def handle_friend_added(sender, user, friend, **kwargs):
        grant_achievement(user, 'first_friend')
        grant_achievement(friend, 'first_friend')
        
        try:
            from plugins.social.models import Friendship
            from django.db import models
            friends_count = Friendship.objects.filter(
                models.Q(user=user, status='ACCEPTED') | models.Q(friend=user, status='ACCEPTED')
            ).count()
            if friends_count >= 50:
                grant_achievement(user, 'friend_50')
        except Exception:
            pass

        try:
            from plugins.social.models import Friendship
            from django.db import models
            friends_count_friend = Friendship.objects.filter(
                models.Q(user=friend, status='ACCEPTED') | models.Q(friend=friend, status='ACCEPTED')
            ).count()
            if friends_count_friend >= 50:
                grant_achievement(friend, 'friend_50')
        except Exception:
            pass


try:
    from plugins.activity.views import movie_watched_signal
except ImportError:
    movie_watched_signal = None

if movie_watched_signal:
    @receiver(movie_watched_signal)
    def handle_movie_watched(sender, user, movie, seconds, **kwargs):
        grant_achievement(user, 'movie_buff')
        
        try:
            from plugins.activity.models import ViewingHistory
            watched_count = ViewingHistory.objects.filter(user=user).count()
            if watched_count >= 100:
                grant_achievement(user, 'movies_100')
        except Exception:
            pass
