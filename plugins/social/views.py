from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db import models
from .models import Friendship
from django.dispatch import Signal

friend_added_signal = Signal()

User = get_user_model()

class FriendsListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        friendships = Friendship.objects.filter(
            models.Q(user=request.user, status='ACCEPTED') | models.Q(friend=request.user, status='ACCEPTED')
        )
        
        friends = []
        for fs in friendships:
            other_user = fs.friend if fs.user == request.user else fs.user
            friends.append({
                "id": other_user.id,
                "username": other_user.username,
                "display_name": other_user.display_name,
                "avatar": other_user.avatar.url if other_user.avatar else None,
                "is_pro": other_user.is_pro,
            })
            
        return Response(friends)


class AddFriendView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        friend_id = request.data.get('friend_id')
        friend_username = request.data.get('username')

        if friend_id:
            try:
                friend_user = User.objects.get(id=friend_id)
            except User.DoesNotExist:
                return Response({"error": "User with this ID does not exist"}, status=404)
        elif friend_username:
            try:
                friend_user = User.objects.get(username=friend_username)
            except User.DoesNotExist:
                return Response({"error": "User with this username does not exist"}, status=404)
        else:
            return Response({"error": "friend_id or username is required"}, status=400)

        if friend_user == request.user:
            return Response({"error": "You cannot add yourself as a friend"}, status=400)

        existing = Friendship.objects.filter(
            models.Q(user=request.user, friend=friend_user) | models.Q(user=friend_user, friend=request.user)
        ).first()

        if existing:
            if existing.status == 'ACCEPTED':
                return Response({"message": "Already friends"}, status=200)
            elif existing.user == request.user:
                return Response({"message": "Friend request already sent"}, status=200)
            else:
                existing.status = 'ACCEPTED'
                existing.save()
                friend_added_signal.send(sender=Friendship, user=request.user, friend=friend_user)
                return Response({"message": "Friend request accepted", "status": "ACCEPTED"}, status=200)

        friendship = Friendship.objects.create(user=request.user, friend=friend_user, status='PENDING')
        return Response({"message": "Friend request sent", "status": "PENDING"}, status=201)


class AcceptFriendView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        from_user_id = request.data.get('user_id')
        if not from_user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            from_user = User.objects.get(id=from_user_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist"}, status=404)

        try:
            friendship = Friendship.objects.get(user=from_user, friend=request.user, status='PENDING')
        except Friendship.DoesNotExist:
            return Response({"error": "Pending friend request not found"}, status=404)
        
        friendship.status = 'ACCEPTED'
        friendship.save()

        friend_added_signal.send(sender=Friendship, user=request.user, friend=from_user)

        return Response({"message": "Friend request accepted"})


class RemoveFriendView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        friend_id = request.data.get('friend_id')
        if not friend_id:
            return Response({"error": "friend_id is required"}, status=400)

        try:
            friend_user = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist"}, status=404)

        friendship = Friendship.objects.filter(
            models.Q(user=request.user, friend=friend_user) | models.Q(user=friend_user, friend=request.user)
        ).first()

        if not friendship:
            return Response({"error": "Friendship not found"}, status=404)

        friendship.delete()
        return Response({"message": "Friend removed successfully"})
