from django.dispatch import receiver
from django.db.models import F
from django.db import IntegrityError, transaction
from apps.rooms.signals import socket_message_signal
from .models import ReactionStat

@receiver(socket_message_signal)
def handle_reaction(sender, room_id, user, message_type, data, **kwargs):
    if message_type == 'reaction.send':
        emoji = data.get('emoji')
        if emoji:

            updated = ReactionStat.objects.filter(room_id=room_id, emoji=emoji).update(count=F('count') + 1)
            if not updated:
                try:
                    with transaction.atomic():
                        ReactionStat.objects.create(room_id=room_id, emoji=emoji, count=1)
                except IntegrityError:
                    ReactionStat.objects.filter(room_id=room_id, emoji=emoji).update(count=F('count') + 1)
            print(f"Reaction Plugin: User sent {emoji}")