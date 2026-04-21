from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Room, RoomMember
from .serializers import RoomSerializer
from .signals import room_created_signal

class RoomCreateView(generics.CreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        room = serializer.save(creator=self.request.user)
        
        RoomMember.objects.create(room=room, user=self.request.user)
        
        room_created_signal.send(
            sender=self.__class__, 
            room_id=room.id, 
            raw_data=self.request.data
        )


class RoomJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            room = Room.objects.get(pk=pk, is_active=True)
        except Room.DoesNotExist:
            return Response(
                {'detail': 'Кімната не знайдена або неактивна.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        _member, created = RoomMember.objects.get_or_create(room=room, user=request.user)
        data = RoomSerializer(room).data
        return Response(
            data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )