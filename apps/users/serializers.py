from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.apps import apps
from django.db import models

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )


class UserProfileSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'display_name', 'avatar', 'bio', 'is_pro', 'date_joined',
            'stats', 'recent_activity', 'achievements'
        ]
        read_only_fields = ['id', 'username', 'email', 'date_joined', 'stats', 'recent_activity', 'achievements']

    def get_stats(self, obj):
        stats = {
            "watched_count": 0,
            "watched_hours": 0.0,
            "rooms_count": obj.created_rooms.count(),
            "friends_count": 0,
        }
        
        if apps.is_installed('plugins.activity'):
            try:
                from plugins.activity.models import ViewingHistory
                stats["watched_count"] = ViewingHistory.objects.filter(user=obj).count()
                total_seconds = ViewingHistory.objects.filter(user=obj).aggregate(models.Sum('watched_seconds'))['watched_seconds__sum'] or 0
                stats["watched_hours"] = round(total_seconds / 3600.0, 1)
            except Exception:
                pass

        if apps.is_installed('plugins.social'):
            try:
                from plugins.social.models import Friendship
                stats["friends_count"] = Friendship.objects.filter(
                    models.Q(user=obj, status='ACCEPTED') | models.Q(friend=obj, status='ACCEPTED')
                ).count()
            except Exception:
                pass

        return stats

    def get_recent_activity(self, obj):
        activities = []
        if apps.is_installed('plugins.activity'):
            try:
                from plugins.activity.models import ViewingHistory
                history = ViewingHistory.objects.filter(user=obj).order_by('-watched_at')[:10]
                for item in history:
                    movie_title = item.movie.title if item.movie else "Unknown Movie"
                    activities.append({
                        "id": str(item.id),
                        "movie_title": movie_title,
                        "room_id": str(item.room_id) if item.room_id else None,
                        "watched_at": item.watched_at.isoformat(),
                        "watched_seconds": item.watched_seconds,
                    })
            except Exception:
                pass
        return activities

    def get_achievements(self, obj):
        achs = []
        if apps.is_installed('plugins.achievements'):
            try:
                from plugins.achievements.models import Achievement, UserAchievement
                
                # Define all standard achievements in the system
                ALL_ACHIEVEMENTS = {
                    "first_room": ("Перша кімната", "Ви створили свою першу кімнату для перегляду!", "crown"),
                    "first_friend": ("Перший друг", "Додано першого друга до вашої кінокомпанії!", "heart"),
                    "movie_buff": ("Кіноман", "Ви переглянули свій перший фільм!", "fire"),
                    "streak_7": ("Сім днів", "Активність протягом 7 днів поспіль!", "streak_7"),
                    "movies_100": ("Кіномарафон", "Ви переглянули 100 фільмів!", "movies_100"),
                    "friend_50": ("Душа компанії", "У вас 50 друзів!", "friend_50"),
                }
                
                for key, (name, desc, icon) in ALL_ACHIEVEMENTS.items():
                    Achievement.objects.get_or_create(
                        key=key,
                        defaults={"name": name, "description": desc, "icon": icon}
                    )
                
                all_achs = Achievement.objects.all().order_by('id')
                user_achs = {ua.achievement_id: ua for ua in UserAchievement.objects.filter(user=obj)}
                
                for ach in all_achs:
                    earned = ach.id in user_achs
                    achs.append({
                        "id": str(ach.id),
                        "name": ach.name,
                        "key": ach.key,
                        "description": ach.description,
                        "icon": ach.icon,
                        "earned": earned,
                        "earned_at": user_achs[ach.id].earned_at.isoformat() if earned else None,
                    })
            except Exception:
                pass
        return achs