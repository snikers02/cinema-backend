from django.urls import path
from .views import RoomCreateView, RoomJoinView

urlpatterns = [
    path('', RoomCreateView.as_view(), name='room-create'),
    path('<uuid:pk>/join/', RoomJoinView.as_view(), name='room-join'),
]