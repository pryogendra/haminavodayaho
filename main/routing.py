from django.urls import path #type: ignore
from . import consumers
from . import CustomRequest

websocket_urlpatterns = [
    path('ws/chat/<str:sender>/<str:receiver>',consumers.MessageConsumers.as_asgi()),
    path('ws/inbox/<str:phone>', consumers.InboxConsumers.as_asgi()),
    path('ws/call/<str:caller>/<str:callee>', consumers.AudioCallConsumer.as_asgi()),
    path('ws/getComments/<str:phone>/<str:id>', consumers.GetCommentConsumers.as_asgi()),

    path('ws/custom/<str:phone>', CustomRequest.UserActivityConsumer.as_asgi()),
    
]