from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from plugins.movies.models import Movie
from .models import ViewingHistory
from django.dispatch import Signal

movie_watched_signal = Signal()

class RecordActivityView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        movie_id = request.data.get('movie_id')
        room_id = request.data.get('room_id')
        seconds = int(request.data.get('seconds', 0))

        if not movie_id:
            return Response({"error": "movie_id is required"}, status=400)

        movie = get_object_or_404(Movie, id=movie_id)
        
        history_record = ViewingHistory.objects.create(
            user=request.user,
            movie=movie,
            room_id=room_id,
            watched_seconds=seconds
        )

        movie_watched_signal.send(
            sender=ViewingHistory,
            user=request.user,
            movie=movie,
            seconds=seconds
        )

        return Response({
            "message": "Activity recorded successfully",
            "watched_count": ViewingHistory.objects.filter(user=request.user).count()
        })
