from django.urls import path
from .views import RoomListCreateView, RoomJoinView, JoinByCodeView, MyRoomsListView, RoomDetailView

urlpatterns = [
    path('', RoomListCreateView.as_view(), name='room-list-create'), 
    path('<uuid:pk>/join/', RoomJoinView.as_view(), name='room-join'),
    path('join-by-code/', JoinByCodeView.as_view(), name='join-by-code'),
    path('my/', MyRoomsListView.as_view()),
    path('<uuid:pk>/', RoomDetailView.as_view(), name='room-detail'),
]