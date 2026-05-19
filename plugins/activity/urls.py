from django.urls import path
from .views import RecordActivityView

urlpatterns = [
    path('record/', RecordActivityView.as_view(), name='record_activity'),
]
