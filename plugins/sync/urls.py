from django.urls import path
from .views import RoomRulesView, GrantControlView, RevokeControlView

urlpatterns = [
    path('rules/<uuid:room_id>/', RoomRulesView.as_view(), name='sync-rules'),
    path('rules/<uuid:room_id>/grant/', GrantControlView.as_view(), name='sync-rules-grant'),
    path('rules/<uuid:room_id>/revoke/', RevokeControlView.as_view(), name='sync-rules-revoke'),
]
