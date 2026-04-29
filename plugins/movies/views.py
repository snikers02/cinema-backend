from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Movie, RoomVideo
from .serializers import MoviesSerializer, RoomWithMovieSerializer

# 1. Завантаження та перегляд списку фільмів користувача
class MovieListCreateView(generics.ListCreateAPIView):
    serializer_class = MoviesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Movie.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

# 2. Отримання фільму для конкретної кімнати (коли юзер заходить в кімнату)
class RoomMovieDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, room_id):
        try:
            room_video = RoomVideo.objects.get(room_id=room_id)
            return Response({
                "room_id": room_id,
                "movie": MoviesSerializer(room_video.movie).data
            })
        except RoomVideo.DoesNotExist:
            return Response({"error": "No movie for this room"}, status=status.HTTP_404_NOT_FOUND)

# 3. Список УСІХ активних кімнат з їхніми фільмами (для головної сторінки/карток)
class ActiveRoomsWithMoviesView(generics.ListAPIView):
    queryset = RoomVideo.objects.filter(is_public=True).select_related('movie')
    serializer_class = RoomWithMovieSerializer
    permission_classes = [permissions.AllowAny]