from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Message, Like, Comment, Share, CallRecord

channel_layer = get_channel_layer()

def notify_user(receiver_profile, message):
    group_name = f"custom_user_{receiver_profile.phone_number.replace("+", "_").replace("@", "_")}"
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "data": {
                "message": message
            }
        }
    )
@receiver(post_save, sender=Message)
def notify_on_new_message(sender, instance, created, **kwargs):
    if created:
        notify_user(instance.receiver, f"📨 New message from {instance.sender.username}")

@receiver(post_save, sender=Like)
def notify_on_new_like(sender, instance, created, **kwargs):
    if created:
        notify_user(instance.post.profile, f"👍 Your post was liked by {instance.profile.username}")

@receiver(post_save, sender=Comment)
def notify_on_new_comment(sender, instance, created, **kwargs):
    if created:
        notify_user(instance.post.profile, f"💬 New comment on your post by {instance.profile.username}")

@receiver(post_save, sender=Share)
def notify_on_new_share(sender, instance, created, **kwargs):
    if created:
        notify_user(instance.post.profile, f"🔁 Your post was shared by {instance.profile.username}")

# @receiver(post_save, sender=CallRecord)
# def notify_on_new_call(sender, instance, created, **kwargs):
#     if created:
#         notify_user(instance.receiver, f"📞 Incoming {instance.call_type} call from {instance.caller.username}")
