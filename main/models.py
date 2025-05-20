from django.db import models
from datetime import datetime

class Profile(models.Model):
    phone_number = models.CharField(primary_key=True, max_length=100)
    username = models.CharField(max_length=255, default="User")
    email = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    category = models.CharField(max_length=1000, null=True, default = "Student")
    bio = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=555, null=True, blank=True)
    
    pg_institute = models.TextField(default="None", null=True, blank=True)
    pg_year = models.TextField(default="None",null=True, blank=True)
    
    ug_institute = models.TextField(default="None",null=True, blank=True)
    ug_year = models.TextField(default="None",null=True, blank=True)
    
    school = models.TextField(default="None",null=True, blank=True)
    school_year = models.TextField(default="None",null=True, blank=True)

    document = models.FileField(null=True, blank=True)
    tags = models.CharField(max_length=255, default="user", blank=True, help_text="Comma-separated tags")
    important = models.BooleanField(default=False)

    def __str__(self):
        return self.phone_number


class Event(models.Model):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    data = models.FileField(upload_to='event/', null= True, blank= True)
    description = models.TextField(null= True, blank= True)
    url = models.TextField(blank=True, null=True)
    date = models.DateTimeField(default= None, blank= True, null= True)
    important = models.BooleanField(default= False)
    def __str__(self):
        return self.profile.phone_number
    
class EventClicked(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)


class Post(models.Model):
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateTimeField(default= None, blank= True)
    data = models.FileField(upload_to='post/', null= True, blank= True)
    description = models.TextField(null= True, blank= True)
    support_count = models.BigIntegerField(default=0, blank=True, null=True)
    comment_count = models.BigIntegerField(default=0, blank=True, null=True)
    share_count = models.BigIntegerField(default=0, blank=True, null=True)
    important = models.BooleanField(default= False)
    def __str__(self):
        return self.profile.phone_number
    
class Like(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateTimeField(default=None, blank=True)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    message = models.TextField(null= True, blank=True)
    date = models.DateTimeField(default=None, blank=True)

class Share(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateTimeField(default=None, blank=True)
    
class Message(models.Model):
    id = models.BigAutoField(primary_key=True)
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sender')
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='receiver')
    data = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(default= None, blank= True)
    status = models.BooleanField(default= False)
    is_send = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.sender} => {self.receiver} =>{self.data}"
    
class Inbox(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE)
    receiver = models.ForeignKey(Profile, on_delete= models.CASCADE, related_name= 'contact')
    unread_count = models.BigIntegerField(default=0, blank= True, null= True)
    def __str__(self):
        return f"{self.sender} => {self.receiver}"

class CallRecord(models.Model):
    CALL_TYPE_CHOICES = (
        ('audio', 'Audio'),
        ('video', 'Video'),
    )
    STATUS_CHOICES = (
        ('missed', 'Missed'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('ongoing', 'Ongoing'),
    )

    caller = models.ForeignKey(Profile, related_name='outgoing_calls', on_delete=models.CASCADE)
    receiver = models.ForeignKey(Profile, related_name='incoming_calls', on_delete=models.CASCADE)
    call_type = models.CharField(max_length=10, choices=CALL_TYPE_CHOICES, default='audio')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ongoing')
    start_time = models.DateTimeField(default=None, blank=True)
    end_time = models.DateTimeField(default=None, blank=True)

    def duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def __str__(self):
        return f"{self.caller} ➔ {self.receiver} [{self.call_type}]"

