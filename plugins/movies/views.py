from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Movie
from .serializers import MovieSerializer
from rest_framework.views import APIView
from .models import RoomVideo
from rest_framework import status
from rest_framework.response import Response


class MovieListCreateView(generics.ListCreateAPIView):
    serializer_class = MovieSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Movie.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RoomMovieDetailView(APIView):
    def get(self, request, room_id):
        try:
            room_video = RoomVideo.objects.get(room_id=room_id)
            return Response({
                "room_id": room_id,
                "movie": MovieSerializer(room_video.movie).data
            })
        except RoomVideo.DoesNotExist:
            return Response({"error": "No movie for this room"}, status=404)