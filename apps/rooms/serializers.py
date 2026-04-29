from rest_framework import serializers
from .models import Room, RoomMember

class RoomMemberSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = RoomMember
        fields = ['user', 'username', 'joined_at']

class RoomSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source='creator.username')
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            'id', 
            'name', 
            'is_public',
            'invite_code',
            'creator', 
            'creator_name', 
            'members_count', 
            'created_at'
        ]
        read_only_fields = [
            'id', 
            'creator', 
            'creator_name', 
            'invite_code',
            'created_at'
        ]

    def get_members_count(self, obj):
        # Перевірка на всяк випадок, якщо об'єкт ще не створений
        if hasattr(obj, 'members'):
            return obj.members.count()
        return 0