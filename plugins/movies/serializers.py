from rest_framework import serializers
from .models import Movie, RoomVideo

class MoviesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'video_type', 'video_file', 'youtube_url', 'poster', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        video_type = attrs.get('video_type', 'FILE')
        
        if video_type == 'FILE':
            video_file = attrs.get('video_file')
            if not video_file:
                if not self.instance:
                    raise serializers.ValidationError({"video_file": "This field is required for file streaming."})
            else:
                if not video_file.name.lower().endswith(('.mp4', '.mkv', '.avi', '.webm')):
                    raise serializers.ValidationError({"video_file": "Unsupported video format."})
            attrs['youtube_url'] = None
            
        elif video_type == 'YOUTUBE':
            youtube_url = attrs.get('youtube_url')
            if not youtube_url:
                raise serializers.ValidationError({"youtube_url": "This field is required for YouTube streaming."})
            if 'youtube.com' not in youtube_url.lower() and 'youtu.be' not in youtube_url.lower():
                raise serializers.ValidationError({"youtube_url": "Invalid YouTube URL format."})
            attrs['video_file'] = None
            
        return attrs

class RoomWithMovieSerializer(serializers.ModelSerializer):
    movie_details = MoviesSerializer(source='movie', read_only=True)

    class Meta:
        model = RoomVideo
        fields = ['room_id', 'creator_name', 'room_name', 'invite_code', 'movie_details']