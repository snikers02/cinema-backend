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



class RoomSerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source='creator.username')
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'name', 'creator', 'creator_name', 'members_count', 'created_at']
        read_only_fields = ['id', 'creator', 'created_at']

    def get_members_count(self, obj):
        return obj.members.count()