from django.dispatch import receiver
from apps.rooms.signals import socket_message_signal
from .models import ChatMessage

@receiver(socket_message_signal)
def handle_chat_message(sender, room_id, user, message_type, data, **kwargs):
    # Плагін сам вирішує, чи цікаве йому це повідомлення
    if message_type == 'chat.message':
        text = data.get('text')
        if text and user.is_authenticated:
            ChatMessage.objects.create(
                room_id=room_id,
                user=user,
                text=text
            )
            print(f"Chat Plugin: Saved message from {user.username}")