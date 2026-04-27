from django.urls import path
from .views import MovieListCreateView, RoomMovieDetailView, ActiveRoomsWithMoviesView

urlpatterns = [
    path('', MovieListCreateView.as_view(), name='movie-list-create'),
    path('room/<uuid:room_id>/', RoomMovieDetailView.as_view(), name='room-movie-detail'),
    path('active-rooms/', ActiveRoomsWithMoviesView.as_view(), name='active-rooms-movies'),
]