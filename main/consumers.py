import json
from asgiref.sync import sync_to_async # type: ignore
from channels.generic.websocket import AsyncWebsocketConsumer # type: ignore
from django.utils import timezone
from channels.layers import get_channel_layer
from django.db.models import Q
from .models import *
from datetime import datetime

custom_user_channel_layer = get_channel_layer()

class MessageConsumers(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender_user = None
        self.receiver_user = None
        
    async def connect(self):
        self.url = self.scope['url_route']
        self.sender = self.scope['url_route']['kwargs']['sender']
        self.receiver = self.scope['url_route']['kwargs']['receiver']
        self.room_name = 'message' + self.sender.replace("+", "_").replace("@", "_")
        self.room_group_name = self.room_name

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        self.sender_user = await sync_to_async(Profile.objects.get)(phone_number=self.sender)
        self.receiver_user = await sync_to_async(Profile.objects.get)(phone_number=self.receiver)
        
        
        # Fetch the latest 50 messages
        messages = await self.get_messages(offset=0)
        await self.send(text_data=json.dumps({
            'type': 'initial',
            'messages': messages
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']
        
        if message_type == 'chat':
            await self.handle_chat_message(data)
        elif message_type == 'scroll':
            offset = data['offset']
            messages = await self.get_messages(offset)
            await self.send(text_data=json.dumps({
                'type': 'scroll',
                'messages': messages
            }))
    
    async def handle_chat_message(self, data):
        send_data = data['send_data']
                
        # Create the message
        message = await sync_to_async(Message.objects.create)(
            sender=self.sender_user,
            receiver=self.receiver_user,
            data=send_data,
            timestamp = datetime.now(),
        )

        inbox, created = await sync_to_async(Inbox.objects.get_or_create)(
            sender=self.sender_user,
            receiver=self.receiver_user,
            defaults={'unread_count': 1}
        )
        if not created:
            inbox.unread_count += 1
            await sync_to_async(inbox.save)()
            
        inbox2, created2 = await sync_to_async(Inbox.objects.get_or_create)(
            sender=self.receiver_user,
            receiver=self.sender_user,
            defaults={'unread_count': 0}
        )
        if not created2:
            await sync_to_async(inbox2.save)()
            
        # Send message to the receiver's group
        receiver_group = f"message{self.receiver.replace('+', '_').replace('@', '_')}"
        await self.channel_layer.group_send(
            receiver_group,
            {
                "type": "chat_message",
                "sender": self.sender,
                "receiver": self.receiver,
                "send_data": send_data,
                "timestamp": str(message.timestamp.strftime("%I:%M %p")),
                "message_id": str(message.id),
            })
        
        #send the message to the sender
        await self.send(text_data=json.dumps({
            "type": "chat",
            "sender": self.sender,
            "receiver": self.receiver,
            "send_data": send_data,
            "timestamp": str(message.timestamp.strftime("%I:%M %p")),
            "message_id": str(message.id),
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type' : 'chat',
            "sender": event['sender'],
            "receiver": event['receiver'],
            "send_data": event['send_data'],
            "timestamp": event.get("timestamp"),
            "message_id": event.get("message_id"),
        }))
            
    async def get_messages(self, offset=0):
        @sync_to_async
        def fetch_messages():
            return list(
                Message.objects.filter(
                    (Q(sender__phone_number=self.sender_user) & Q(receiver__phone_number=self.receiver_user)) |
                    (Q(sender__phone_number=self.receiver_user) & Q(receiver__phone_number=self.sender_user))
                ).order_by('-timestamp')[offset:offset + 30]
            )

        @sync_to_async
        def serialize_messages(messages):
            return [{
                'sender': msg.sender.phone_number,
                'receiver': msg.receiver.phone_number,
                'send_data': msg.data,
                'timestamp': str(msg.timestamp.strftime("%I:%M %p")),
                'message_id': str(msg.id),
            } for msg in messages]

        messages = await fetch_messages()
        try:
            ind = await sync_to_async(Inbox.objects.get)(sender = self.receiver_user, receiver = self.sender_user)
            ind.unread_count = 0
            await sync_to_async(ind.save)()
        except Exception as e:
            print("Error : ",e)
        return await serialize_messages(reversed(messages))

def get_last_message(user1, user2):
    messages1 = Message.objects.filter(sender=user1, receiver=user2)
    messages2 = Message.objects.filter(sender=user2, receiver=user1)
    
    all_messages = messages1.union(messages2).order_by('-timestamp')
    return all_messages.first()
            
class InboxConsumers(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.phone_number = None

    async def connect(self):
        self.phone_number = self.scope['url_route']['kwargs']['phone']
        from .models import Profile
        try:
            self.user = await sync_to_async(Profile.objects.get)(phone_number=self.phone_number)
            await self.accept()
            await self.send_inbox_data()
        except Profile.DoesNotExist:
            await self.close()

    async def disconnect(self, close_code):
        pass
    async def receive(self, text_data):
        pass
    async def send_inbox_data(self):
        try:          
            @sync_to_async
            def get_distinct_users(current_user):
                sent_inboxes = Inbox.objects.filter(sender=current_user).exclude(receiver=current_user)
                received_inboxes = Inbox.objects.filter(receiver=current_user).exclude(sender=current_user)
                users = set()
                for inbox in sent_inboxes:
                    users.add(inbox.receiver)
                for inbox in received_inboxes:
                    users.add(inbox.sender)
                data =[]
                for user in users:
                    msg = get_last_message(user, self.user)
                    try:
                        unread_count_user = Inbox.objects.get(sender = user, receiver = current_user)
                    except:
                        pass
                    data.append({
                        'phone' : user.phone_number,
                        'profile': user.profile_picture.url if user.profile_picture else None,
                        'username': user.username,
                        'last_message' : msg.data,
                        'unread_count': unread_count_user.unread_count,
                    })
                return data

            if self.user:
                inbox_data = await get_distinct_users(self.user)
                await self.send(text_data=json.dumps(inbox_data))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f"Error fetching inbox data: {str(e)}"}))
            print("Error Inbox",e)

class GetCommentConsumers(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.id = None
        
    async def connect(self):
        self.phone = self.scope['url_route']['kwargs']['phone']
        self.id = self.scope['url_route']['kwargs']['id']
        
        
        await self.accept()
        self.user = sync_to_async(Profile.objects.get)(phone_number = self.phone)
        
        await self.send_comment_data()
    
    async def disconnect(self, close_code):
        pass
    async def receive(self, text_data):
        pass
    
    async def send_comment_data(self):
        post = await sync_to_async(Post.objects.get)(id = self.id)
            
        comments = await sync_to_async(lambda: list(Comment.objects.filter(post = post).select_related('post','profile')))()
        com_data = [{
            'id': com.post.id,
            'user': com.profile.username,
            'phone': com.profile.phone_number,
            'message': com.message,
            'date': str(com.date.strftime("%Y-%m-%d %I:%M %p")),
        } for com in comments]
        await self.send(text_data = json.dumps({'data':com_data}))

class AudioCallConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender_user = None
        self.receiver_user = None
        
    async def connect(self):
        self.caller = self.scope['url_route']['kwargs']['caller']
        self.callee = self.scope['url_route']['kwargs']['callee']
        self.room_group_name = f'audio_call_{self.caller.replace("+", "_").replace("@", "_")}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        self.sender_user = await sync_to_async(Profile.objects.get)(phone_number = self.caller)
        self.receiver_user = await sync_to_async(Profile.objects.get)(phone_number = self.callee)
        
        print(f"{self.caller} is calling {self.callee}")

        custom_user_group_name = f"custom_user_{self.receiver_user.phone_number.replace("+", "_").replace("@", "_")}"
        await custom_user_channel_layer.group_send(
            custom_user_group_name,
            {
                "type": "send_notification",
                "data": {
                    "message": "calling",
                    "caller" : self.caller,
                    "name" : self.sender_user.username,
                    "profile" : self.sender_user.profile
                }
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # await self.receiver_user.send(text_data = json.dumps(text_data))
        # return
        
        # if target in connected_users:
        #     await connected_users[target].send(text_data=json.dumps(data))


        message_type = data.get('type')

        if message_type == 'start_call':
            await sync_to_async(CallRecord.objects.create)(
                caller=self.sender_user,
                receiver=self.receiver_user,
                call_type="audio",
                status='ongoing',
                start_time = datetime.now(),
            )
        elif message_type == 'end_call':
            await sync_to_async(CallRecord.objects.filter(
                caller=self.sender_user,
                receiver=self.receiver_user,
                status='ongoing'
            ).update)(
                status='completed',
                end_time=datetime.now()
            )
        elif message_type == 'accept':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_accepted',
                    'message': 'Call accepted by callee'
                }
            )
        elif message_type == 'reject':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_rejected',
                    'message': 'Call rejected by callee'
                }
            )
        elif message_type in ['offer', 'answer', 'ice']:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'audio_call_message',
                    'message': data
                }
            )

    async def call_accepted(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message,
            'type': 'call_accepted'
        }))

    async def call_rejected(self, event):
        message = event['message']
        # Notify the caller that the callee has rejected the call
        await self.send(text_data=json.dumps({
            'message': message,
            'type': 'call_rejected'
        }))

    async def audio_call_message(self, event):
        message = event['message']
        print("-------------------------------")
        print(message)

        await self.send(text_data=json.dumps({
            'message': message
        }))
