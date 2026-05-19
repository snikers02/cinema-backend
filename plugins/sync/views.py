from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.rooms.models import Room  # type: ignore
from apps.users.models import CustomUser  # type: ignore
from .models import RoomPlaybackRules, RoomAuthorizedController, check_user_can_control_playback
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def _notify_room_rules_updated(room_id, rules):
    controllers = RoomAuthorizedController.objects.filter(room_id=room_id).select_related('user')
    auth_list = [{"userId": c.user.id, "username": c.user.username} for c in controllers]
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"room_{room_id}",
        {
            "type": "room_broadcast",
            "payload": {
                "type": "sync_rules_updated",
                "anyone_can_control": rules.anyone_can_control,
                "authorized_users": auth_list
            }
        }
    )

class RoomRulesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        rules, _ = RoomPlaybackRules.objects.get_or_create(
            room_id=room_id,
            defaults={'anyone_can_control': False}
        )
        controllers = RoomAuthorizedController.objects.filter(room_id=room_id).select_related('user')
        auth_list = [{"userId": c.user.id, "username": c.user.username} for c in controllers]
        
        can_control = check_user_can_control_playback(request.user, room_id)

        return Response({
            "room_id": room_id,
            "anyone_can_control": rules.anyone_can_control,
            "authorized_users": auth_list,
            "can_control": can_control
        })

    def post(self, request, room_id):
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        if room.creator != request.user:
            return Response({"error": "Only room creator can change rules"}, status=status.HTTP_403_FORBIDDEN)

        anyone_can_control = request.data.get('anyone_can_control', False)
        
        rules, _ = RoomPlaybackRules.objects.get_or_create(
            room_id=room_id,
            defaults={'anyone_can_control': False}
        )
        rules.anyone_can_control = bool(anyone_can_control)
        rules.save()

        _notify_room_rules_updated(room_id, rules)

        controllers = RoomAuthorizedController.objects.filter(room_id=room_id).select_related('user')
        auth_list = [{"userId": c.user.id, "username": c.user.username} for c in controllers]

        return Response({
            "room_id": room_id,
            "anyone_can_control": rules.anyone_can_control,
            "authorized_users": auth_list,
            "can_control": True
        })

class GrantControlView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        if room.creator != request.user:
            return Response({"error": "Only room creator can grant control rights"}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        username = request.data.get('username')

        if not user_id and not username:
            return Response({"error": "user_id or username is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if user_id:
                target_user = CustomUser.objects.get(id=user_id)
            else:
                target_user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response({"error": "Target user not found"}, status=status.HTTP_404_NOT_FOUND)

        if target_user == room.creator:
            return Response({"message": "Owner already has control"}, status=status.HTTP_200_OK)

        RoomAuthorizedController.objects.get_or_create(
            room_id=room_id,
            user=target_user
        )

        rules, _ = RoomPlaybackRules.objects.get_or_create(
            room_id=room_id,
            defaults={'anyone_can_control': False}
        )

        _notify_room_rules_updated(room_id, rules)

        controllers = RoomAuthorizedController.objects.filter(room_id=room_id).select_related('user')
        auth_list = [{"userId": c.user.id, "username": c.user.username} for c in controllers]

        return Response({
            "room_id": room_id,
            "anyone_can_control": rules.anyone_can_control,
            "authorized_users": auth_list
        })

class RevokeControlView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        if room.creator != request.user:
            return Response({"error": "Only room creator can revoke control rights"}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        RoomAuthorizedController.objects.filter(
            room_id=room_id,
            user_id=user_id
        ).delete()

        rules, _ = RoomPlaybackRules.objects.get_or_create(
            room_id=room_id,
            defaults={'anyone_can_control': False}
        )

        _notify_room_rules_updated(room_id, rules)

        controllers = RoomAuthorizedController.objects.filter(room_id=room_id).select_related('user')
        auth_list = [{"userId": c.user.id, "username": c.user.username} for c in controllers]

        return Response({
            "room_id": room_id,
            "anyone_can_control": rules.anyone_can_control,
            "authorized_users": auth_list
        })
