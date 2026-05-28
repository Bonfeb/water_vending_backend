import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "location_updates"
        self.user = await self.get_user_from_token()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if self.user and not isinstance(self.user, AnonymousUser):
            await self.send(text_data=json.dumps({
                'type': 'connection',
                'message': f'Connected as {self.user.first_name}',
                'user_id': self.user.id
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'location_update':
            await self.update_location(data)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'location_broadcast',
                    'user_id': self.user.id if self.user else None,
                    'lat': data.get('lat'),
                    'lng': data.get('lng'),
                    'accuracy': data.get('accuracy'),
                    'speed': data.get('speed'),
                    'heading': data.get('heading'),
                    'timestamp': data.get('timestamp'),
                    'is_rider': self.user.is_rider if self.user else False
                }
            )

    async def location_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'user_id': event['user_id'],
            'lat': event['lat'],
            'lng': event['lng'],
            'accuracy': event['accuracy'],
            'speed': event['speed'],
            'heading': event['heading'],
            'timestamp': event['timestamp'],
            'is_rider': event['is_rider']
        }))

    @database_sync_to_async
    def get_user_from_token(self):
        try:
            headers = dict(self.scope['headers'])
            auth_header = headers.get(b'authorization', b'').decode()
            if auth_header.startswith('Token '):
                token_key = auth_header.split(' ')[1]
                token = Token.objects.get(key=token_key)
                return token.user
        except:
            pass
        return AnonymousUser()

    @database_sync_to_async
    def update_location(self, data):
        from users.models import User, LocationHistory
        from django.utils import timezone

        if self.user and not isinstance(self.user, AnonymousUser):
            self.user.location_lat = data.get('lat')
            self.user.location_lng = data.get('lng')
            self.user.location_updated_at = timezone.now()
            self.user.save()

            LocationHistory.objects.create(
                user=self.user,
                lat=data.get('lat'),
                lng=data.get('lng'),
                accuracy=data.get('accuracy'),
                speed=data.get('speed'),
                heading=data.get('heading')
            )


class OrderTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.order_group = f"order_{self.order_id}"

        await self.channel_layer.group_add(self.order_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.order_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'rider_location':
            await self.channel_layer.group_send(
                self.order_group,
                {
                    'type': 'rider_location_update',
                    'lat': data.get('lat'),
                    'lng': data.get('lng'),
                    'accuracy': data.get('accuracy'),
                    'timestamp': data.get('timestamp')
                }
            )

    async def rider_location_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'rider_location',
            'lat': event['lat'],
            'lng': event['lng'],
            'accuracy': event['accuracy'],
            'timestamp': event['timestamp']
        }))