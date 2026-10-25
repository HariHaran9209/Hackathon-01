import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class ProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f"project_{self.project_id}"

        # Join project group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send welcome ack
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'project_id': self.project_id,
            'message': 'Connected to live board WebSocket stream.'
        }))

    async def disconnect(self, close_code):
        # Leave project group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming messages from client (e.g. heartbeat or client broadcast).
        """
        if not text_data:
            return
        try:
            data = json.loads(text_data)
            action = data.get('action')
            if action == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception:
            pass

    async def board_message(self, event):
        """
        Forward broadcast event down to WebSocket client.
        """
        await self.send(text_data=json.dumps(event['payload']))


def notify_project_update(project_id: int, event_type: str, data: dict):
    """
    Synchronous helper to broadcast board change notifications across Channel Layer.
    Can be invoked from standard Django views or tasks.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    payload = {
        'type': 'board_message',
        'payload': {
            'event': event_type,
            'project_id': project_id,
            'data': data
        }
    }
    try:
        async_to_sync(channel_layer.group_send)(
            f"project_{project_id}",
            payload
        )
    except Exception as e:
        print(f"[WebSocket Broadcast Error] {e}")
