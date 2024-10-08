import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        messages = await self.get_previous_messages(self.room_name)
        for message in messages:
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': message['content'],
                'username': message['username'],
                'timestamp': message['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']

        await self.save_message(username, self.room_name, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'username': username,
        }))

    @sync_to_async
    def save_message(self, username, room_name, message):
        Message.objects.create(
            username=username, room_name=room_name, content=message)

    @sync_to_async
    def get_previous_messages(self, room_name):
        messages = Message.objects.filter(
            room_name=room_name).order_by('timestamp')
        return [{
            'username': msg.username,
            'content': msg.content,
            'timestamp': msg.timestamp
        } for msg in messages]
