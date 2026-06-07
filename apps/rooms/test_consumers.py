import asyncio
import json
import uuid
from django.test import TestCase, override_settings
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.rooms.consumers import RoomConsumer
from apps.rooms.models import Room
from plugins.sync.models import RoomPlaybackState, RoomPlaybackRules
from plugins.chat.models import ChatMessage
from plugins.reactions.models import ReactionStat
from tests.helpers import create_test_user


@override_settings(
    CHANNEL_LAYERS={'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
)
class RoomConsumerTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username='wsconsumer')
        self.other = create_test_user(username='wsother')
        self.room = Room.objects.create(creator=self.user, name='WS Room')
        self.room_id = str(self.room.id)

    def _make_communicator(self, user=None):
        communicator = WebsocketCommunicator(
            RoomConsumer.as_asgi(),
            f'/ws/room/{self.room_id}/',
        )
        communicator.scope['user'] = user or self.user
        communicator.scope['url_route'] = {'kwargs': {'room_id': self.room_id}}
        return communicator

    async def _connect(self, user=None):
        communicator = self._make_communicator(user)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    async def _collect_messages(self, communicator, timeout=1.0):
        messages = []
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            try:
                remaining = deadline - asyncio.get_event_loop().time()
                raw = await asyncio.wait_for(communicator.receive_from(), max(remaining, 0.05))
                messages.append(json.loads(raw))
            except (asyncio.TimeoutError, TimeoutError):
                break
        return messages

    def test_connect_sends_initial_sync(self):
        RoomPlaybackState.objects.create(room_id=self.room.id, current_time=42.5, is_playing=True)

        async def run():
            comm = await self._connect()
            msg = json.loads(await comm.receive_from())
            await comm.disconnect()
            return msg

        msg = async_to_sync(run)()
        self.assertEqual(msg['type'], 'initial_sync')
        self.assertEqual(msg['time'], 42.5)
        self.assertTrue(msg['is_playing'])

    def test_connect_creates_default_playback_state(self):
        async def run():
            comm = await self._connect()
            await comm.disconnect()

        async_to_sync(run)()
        self.assertTrue(RoomPlaybackState.objects.filter(room_id=self.room.id).exists())

    def test_presence_event_user_joined(self):
        async def run():
            consumer = RoomConsumer()
            sent = []

            async def mock_send(text_data=None):
                sent.append(json.loads(text_data))

            consumer.send = mock_send
            await consumer.presence_event({
                'type': 'presence_event',
                'payload': {'type': 'user_joined', 'username': 'wsother', 'user_id': self.other.id},
            })
            return sent

        sent = async_to_sync(run)()
        self.assertEqual(sent[0]['type'], 'user_joined')
        self.assertEqual(sent[0]['username'], 'wsother')

    def test_presence_event_user_left(self):
        async def run():
            consumer = RoomConsumer()
            sent = []

            async def mock_send(text_data=None):
                sent.append(json.loads(text_data))

            consumer.send = mock_send
            await consumer.presence_event({
                'type': 'presence_event',
                'payload': {'type': 'user_left', 'username': 'wsother'},
            })
            return sent

        sent = async_to_sync(run)()
        self.assertEqual(sent[0]['type'], 'user_left')

    def test_room_broadcast_forwards_payload(self):
        async def run():
            consumer = RoomConsumer()
            consumer.channel_name = 'test_channel'
            sent = []

            async def mock_send(text_data=None):
                sent.append(json.loads(text_data))

            consumer.send = mock_send
            await consumer.room_broadcast({
                'type': 'room_broadcast',
                'payload': {'type': 'play', 'time': 10},
                'sender_channel': 'other_channel',
            })
            return sent

        sent = async_to_sync(run)()
        self.assertEqual(sent[0]['type'], 'play')

    def test_chat_message_saved_via_signal(self):
        import plugins.signals  # noqa: F401 — register chat handler

        async def run():
            comm = await self._connect()
            await comm.receive_from()
            await comm.send_json_to({'type': 'chat.message', 'text': 'Hello WS'})
            await comm.disconnect()

        async_to_sync(run)()
        self.assertTrue(ChatMessage.objects.filter(room_id=self.room.id, text='Hello WS').exists())

    def test_chat_message_adds_username(self):
        received = []

        async def run():
            comm1 = await self._connect(self.user)
            await comm1.receive_from()
            comm2 = self._make_communicator(self.other)
            await comm2.connect()
            await comm2.receive_from()
            await comm1.receive_from()
            await comm2.send_json_to({'type': 'chat.message', 'text': 'Hi'})
            msg = json.loads(await comm1.receive_from())
            await comm1.disconnect()
            await comm2.disconnect()
            return msg

        msg = async_to_sync(run)()
        self.assertEqual(msg.get('username'), 'wsother')

    def test_play_updates_playback_state(self):
        async def run():
            comm = await self._connect(self.user)
            await comm.receive_from()
            await comm.send_json_to({'type': 'play', 'time': 15.0})
            await comm.disconnect()

        async_to_sync(run)()
        state = RoomPlaybackState.objects.get(room_id=self.room.id)
        self.assertTrue(state.is_playing)
        self.assertEqual(state.current_time, 15.0)

    def test_pause_updates_playback_state(self):
        RoomPlaybackState.objects.create(room_id=self.room.id, current_time=10, is_playing=True)

        async def run():
            comm = await self._connect(self.user)
            await comm.receive_from()
            await comm.send_json_to({'type': 'pause', 'time': 20.0})
            await comm.disconnect()

        async_to_sync(run)()
        state = RoomPlaybackState.objects.get(room_id=self.room.id)
        self.assertFalse(state.is_playing)
        self.assertEqual(state.current_time, 20.0)

    def test_play_blocked_for_non_controller(self):
        async def run():
            comm = await self._connect(self.other)
            await comm.receive_from()
            await comm.send_json_to({'type': 'play', 'time': 5.0})
            await comm.disconnect()

        async_to_sync(run)()
        state = RoomPlaybackState.objects.get(room_id=self.room.id)
        self.assertFalse(state.is_playing)

    def test_play_allowed_when_anyone_can_control(self):
        RoomPlaybackRules.objects.create(room_id=self.room.id, anyone_can_control=True)

        async def run():
            comm = await self._connect(self.other)
            await comm.receive_from()
            await comm.send_json_to({'type': 'play', 'time': 7.0})
            await comm.disconnect()

        async_to_sync(run)()
        state = RoomPlaybackState.objects.get(room_id=self.room.id)
        self.assertTrue(state.is_playing)

    def test_reaction_increments_stat(self):
        async def run():
            comm = await self._connect(self.user)
            await comm.receive_from()
            await comm.send_json_to({'type': 'reaction.send', 'emoji': '👍'})
            await comm.disconnect()

        async_to_sync(run)()
        stat = ReactionStat.objects.get(room_id=self.room.id, emoji='👍')
        self.assertEqual(stat.count, 1)

    def test_room_broadcast_skips_sender(self):
        async def run():
            comm = await self._connect(self.user)
            await comm.receive_from()
            await self._collect_messages(comm, timeout=0.3)
            await comm.send_json_to({'type': 'ping', 'value': 1})
            messages = await self._collect_messages(comm, timeout=0.5)
            await comm.disconnect()
            return messages

        messages = async_to_sync(run)()
        self.assertFalse(any(m.get('type') == 'ping' for m in messages))

    def test_anonymous_chat_not_saved(self):
        from django.contrib.auth.models import AnonymousUser
        import plugins.signals  # noqa: F401

        async def run():
            comm = self._make_communicator(AnonymousUser())
            await comm.connect()
            await comm.receive_from()
            await comm.send_json_to({'type': 'chat.message', 'text': 'Anon'})
            await comm.disconnect()

        async_to_sync(run)()
        self.assertFalse(ChatMessage.objects.filter(text='Anon').exists())
