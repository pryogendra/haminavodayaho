import json
from asgiref.sync import sync_to_async # type: ignore
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from datetime import datetime
from .models import *

get_channel_layer = get_channel_layer()

class UserActivityConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
    async def connect(self):
        self.phone = self.scope['url_route']['kwargs']['phone']
        self.group_name = f"custom_user_{self.phone.replace("+", "_").replace("@", "_")}"

        # Join user-specific group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        self.user = await sync_to_async(Profile.objects.get)(phone_number = self.phone)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        print(data)
        type = data.get('type')
        
        #Support/Like
        if type == 'support': 
            id = data.get("id")
            post = await sync_to_async(Post.objects.get)(id = id)
            try:
                like = await sync_to_async(Like.objects.create)(
                    post= post, 
                    profile=self.user, 
                    date = datetime.now()
                    )
                print("Like Added:", like)
                post.support_count +=1
            except:
                like = await sync_to_async(Like.objects.get)(
                    post = post, profile = self.user
                )
                await sync_to_async(like.delete)()
                post.support_count -=1
                print("Like existed and deleted.")
            await sync_to_async(post.save)()
         
        #Comment
        elif type == 'comment':
            id = data.get("id")
            msg = data.get('message')
            post = await sync_to_async(Post.objects.get)(id = id)
            
            comment = await sync_to_async(Comment.objects.create)(
                post = post,
                profile = self.user,
                message = msg,
                date = datetime.now()
            )
            post.comment_count += 1
            await sync_to_async(post.save)()
        
        #Share
        elif type == 'share':
            id = data.get("id")
            post = await sync_to_async(Post.objects.get)(id = id)
            
            share = await sync_to_async(Share.objects.create)(
                post = post,
                profile = self.user,
                date = datetime.now()
            )
            post.share_count += 1
            await sync_to_async(post.save)()
            
        #Get Comment
        elif type == "get_comment":
            id = data.get("id")
            post = await sync_to_async(Post.objects.get)(id = id)
            
            comments = await sync_to_async(lambda: list(Comment.objects.filter(post = post).select_related('post','profile')))()
            com_data = [{
                'id': com.post.id,
                'user': com.profile.username,
                'phone': com.profile.phone_number,
                'message': com.message,
                'date': str(com.date.strftime("%Y-%m-%d %I:%M %p")),
            } for com in comments]
            await self.send(text_data = json.dumps({'type': 'get_comment','data':com_data}))

        elif type == "call":
            caller = data.get('caller')
            action = data.get('action')

            get_group_name = f"audio_call_{caller.replace('+','_').replace('@','_')}"
            await get_channel_layer.group_send(
                get_group_name,
                {
                    "type" : "audio_call_message",
                    'data':{
                        'message' : action
                    }
                })
        print(f"Received from {self.user}: {data}")

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["data"]))

        