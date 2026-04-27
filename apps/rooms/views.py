from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Room, RoomMember
from .serializers import RoomSerializer
from .signals import room_created_signal

# 1. Ендпоінт для списку кімнат (GET) та створення (POST)
class RoomListCreateView(generics.ListCreateAPIView):
    queryset = Room.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = RoomSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        room = serializer.save(creator=self.request.user)
        RoomMember.objects.create(room=room, user=self.request.user)
        
        # Сигнал для плагінів (наприклад, для movies)
        room_created_signal.send(
            sender=self.__class__, 
            room_id=room.id,
            room_name=room.name,
            creator_name=self.request.user.username,
            raw_data=self.request.data
        )

# 2. Ендпоінт для входу в кімнату (POST)
class RoomJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            room = Room.objects.get(pk=pk, is_active=True)
        except Room.DoesNotExist:
            return Response(
                {'detail': 'Кімната не знайдена.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Додаємо юзера в учасники, якщо його там ще немає
        _member, created = RoomMember.objects.get_or_create(room=room, user=request.user)
        data = RoomSerializer(room).data
        return Response(
            data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )