from django.urls import path
from .views import MovieListCreateView, RoomMovieDetailView

urlpatterns = [
    path('', MovieListCreateView.as_view(), name='movie-list-create'),
    path('room/<uuid:room_id>/', RoomMovieDetailView.as_view()),
]