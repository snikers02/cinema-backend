from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Room, RoomMember
from .serializers import RoomSerializer
from .signals import room_created_signal

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
        
        room_created_signal.send(
            sender=self.__class__, 
            room_id=room.id,
            room_name=room.name,
            creator_name=self.request.user.username,
            invite_code=room.invite_code,
            is_public=room.is_public,
            raw_data=self.request.data
        )

    def get_queryset(self):
        return Room.objects.filter(is_active=True, is_public=True).order_by('-created_at')

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

        _member, created = RoomMember.objects.get_or_create(room=room, user=request.user)
        data = RoomSerializer(room).data
        return Response(
            data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )



class JoinByCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('invite_code')
        if not code:
            return Response({"error": "Code is required"}, status=400)

        try:
            room = Room.objects.get(invite_code=code.upper(), is_active=True)
            
            _member, created = RoomMember.objects.get_or_create(room=room, user=request.user)
            
            return Response({
                "message": "Joined successfully",
                "room_id": room.id,
                "room_name": room.name
            }, status=200)
            
        except Room.DoesNotExist:
            return Response({"error": "Invalid invite code"}, status=404)


class MyRoomsListView(generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Room.objects.filter(creator=self.request.user, is_active=True)



class RoomDetailView(generics.RetrieveAPIView):
    queryset = Room.objects.filter(is_active=True)
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]