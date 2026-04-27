from django.urls import path
from .views import RoomListCreateView, RoomJoinView

urlpatterns = [
    path('', RoomListCreateView.as_view(), name='room-list-create'), 
    path('<uuid:pk>/join/', RoomJoinView.as_view(), name='room-join'),
]