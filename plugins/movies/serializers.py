from rest_framework import serializers
from .models import Movie, RoomVideo

class MoviesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'video_file', 'poster', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_video_file(self, value):
        if not value.name.endswith(('.mp4', '.mkv', '.avi')):
            raise serializers.ValidationError("Unsupported video format.")
        return value

class RoomWithMovieSerializer(serializers.ModelSerializer):
    movie_details = MoviesSerializer(source='movie', read_only=True)

    class Meta:
        model = RoomVideo
        fields = ['room_id', 'creator_name', 'room_name', 'movie_details']