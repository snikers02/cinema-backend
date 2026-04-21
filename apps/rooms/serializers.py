from rest_framework import serializers
from .models import Room, RoomMember

class RoomMemberSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = RoomMember
        fields = ['user', 'username', 'joined_at']

class RoomSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = Room
        fields = ['id', 'creator', 'creator_name', 'created_at']
        read_only_fields = ['id', 'creator', 'created_at']

    def create(self, validated_data):
        return Room.objects.create(**validated_data)