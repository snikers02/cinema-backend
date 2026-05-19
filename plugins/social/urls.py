from django.urls import path
from .views import FriendsListView, AddFriendView, AcceptFriendView, RemoveFriendView

urlpatterns = [
    path('', FriendsListView.as_view(), name='friends_list'),
    path('add/', AddFriendView.as_view(), name='add_friend'),
    path('accept/', AcceptFriendView.as_view(), name='accept_friend'),
    path('remove/', RemoveFriendView.as_view(), name='remove_friend'),
]
