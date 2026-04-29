import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from plugins.sync.models import RoomPlaybackState
from apps.rooms.models import Room

class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'room_{self.room_id}'
        self.user = self.scope['user']

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        state = await self.get_room_state(self.room_id)
        await self.send(text_data=json.dumps({
            'type': 'initial_sync',
            'time': state.current_time,
            'is_playing': state.is_playing
        }))


        if self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'presence_event',
                    'payload': {
                        'type': 'user_joined',
                        'username': self.user.username,
                        'user_id': self.user.id
                }
            }
        )


        
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')
        current_time = data.get('time', 0)

        is_owner = await self.is_room_owner(self.user, self.room_id)
        
        if is_owner:
            await self.update_room_state(self.room_id, msg_type, current_time)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_sync',
                    'payload': data
                }
            )
        

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'presence_event',
                    'payload': {
                        'type': 'user_left',
                        'username': self.user.username
                    }
                }
            )

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)



    async def presence_event(self, event):
        await self.send(text_data=json.dumps(event['payload']))
    
    async def broadcast_sync(self, event):
        await self.send(text_data=json.dumps(event['payload']))

    @database_sync_to_async
    def is_room_owner(self, user, room_id):
        if not user.is_authenticated: return False
        return Room.objects.filter(id=room_id, creator=user).exists()

    @database_sync_to_async
    def get_room_state(self, room_id):
        state, _ = RoomPlaybackState.objects.get_or_create(room_id=room_id)
        return state

    @database_sync_to_async
    def update_room_state(self, room_id, msg_type, current_time):
        state, _ = RoomPlaybackState.objects.get_or_create(room_id=room_id)
        state.current_time = current_time
        if msg_type == 'play': state.is_playing = True
        if msg_type == 'pause': state.is_playing = False
        state.save()