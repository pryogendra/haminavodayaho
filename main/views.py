from django.http import HttpResponse # type: ignore
from rest_framework.decorators import api_view # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework import status  #type: ignore
from django.core.mail import send_mail, EmailMultiAlternatives #type: ignore
from rest_framework.pagination import PageNumberPagination #type: ignore
from django.template.loader import render_to_string #type: ignore
from django.conf import settings #type: ignore
from twilio.rest import Client #type: ignore
from asgiref.sync import sync_to_async #type: ignore
from .models import *
import random

OTP = 000000

#send sms to mobile number
def send_sms(to_phone_number, message_body): 
    if not to_phone_number:
        return "Phone number is required"
    
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    # print("Mobile number is : ",to_phone_number)
    try:
        message = client.messages.create(
            to=to_phone_number,
            from_=settings.TWILIO_PHONE_NUMBER,
            body=message_body
        )
        return message
    except Exception as e:
        return e
    
# Create your views here.
def home(request):
    return HttpResponse("WELCOME")

@api_view(['POST'])
def sendMobileOTP(request):
    global OTP
    phone = request.data.get('phone')
    OTP = request.data.get("otp")
    
    if not phone:
        return Response({"error": "Phone number is required"}, status=400)
    
    msg = f"Your OTP is {OTP}. It's valid for 10 minutes. For your security, never share this code with anyone, including our staff."
    message = send_sms(phone, msg)
    
    try:
        status = message.status if hasattr(message, 'status') else str(message)
        if status == "delivered" or status == "sent" or status == "queued":
            return Response({"message": "Message sent successfully!"})
        else:
            return Response({"error": f"Message delivery failed", "status": status}, status=500)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def sendEmailOTP(request):
    email = request.data.get('phone')
    OTP = request.data.get("otp")
    
    if email and OTP:
        text_content = f"Your OTP is {OTP}."
        html_content = render_to_string("main/otp.html", {'otp': OTP,'email': email, 'name': 'User'})
        
        msg = EmailMultiAlternatives(
            "HamiNavodayaHo",
            text_content,
            settings.EMAIL_HOST_USER,
            [email],
        )
        msg.attach_alternative(html_content, "text/html")
        print(OTP)
        
        try:
            msg.send()
        except Exception as e:
            print(e)
            return Response({'message': f'Failed to send email: {str(e)}'}, status=500)

        return Response({'message': 'OTP sent successfully', 'otp': OTP})
    else:
        return Response({'message': 'Email and OTP are required'}, status=400)
    
@api_view(['POST'])
def registerMobile(request):
    phone_number = request.data.get('phone')
    try:
        user = Profile.objects.get(phone_number = phone_number)
        return Response({'message': 'User already exists'}, status = status.HTTP_200_OK)
    except:
        user = Profile.objects.create(phone_number=phone_number)
        return Response({'message': 'User created successfully'}, status= status.HTTP_201_CREATED)

@api_view(['POST'])
def getAllUser(request):
    u = request.data.get('phone')
    curr_user = Profile.objects.get(phone_number = u)
    
    curr_tags = [tag.strip().lower() for tag in curr_user.tags.split(',') if tag.strip()]
    all_user = Profile.objects.exclude(phone_number=curr_user.phone_number)
    
    lst = []
    for user in all_user:
        user_tags = [tag.strip().lower() for tag in user.tags.split(',') if tag.strip()]
        if set(curr_tags) & set(user_tags):
            lst.append({
                'profile' : request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
                'username': user.username,
                'contact' : user.phone_number,
                'category': user.category,
                'location' : user.location,
            })
    random.shuffle(lst)
    return Response({'users' : lst[:30]})

@api_view(['POST'])
def getAllPost(request):
    u = request.data.get('phone')
    curr_user = Profile.objects.get(phone_number=u)
    tags = curr_user.tags
    posts = Post.objects.all()[:50]
    lst = []
    for post in posts:
        if any(tag in post.profile.tags for tag in tags) or post.important:
            support = False
            try:
                like = Like.objects.get(post = post, profile = curr_user)
                support = (True if like else False)
            except:
                pass
            
            lst.append({
                'post_id': post.id,
                'profile': request.build_absolute_uri(post.profile.profile_picture.url) if post.profile.profile_picture else None,
                'username': post.profile.username,
                'contact': post.profile.phone_number,
                'data': request.build_absolute_uri(post.data.url) if post.data else None,
                'description': post.description,
                'date': post.date.strftime("%Y-%m-%d %I:%M %p"),
                'support_count':post.support_count,
                'comment_count': post.comment_count,
                'share_count': post.share_count,
                'support' : support,
            })
    random.shuffle(lst)
    return Response({'posts': lst[:25]})

@api_view(['POST'])
def getAllEvent(request):
    u = request.data.get('phone')
    curr_user = Profile.objects.get(phone_number=u)
    tags = curr_user.tags
    
    events = Event.objects.all()[:50]
    lst = []
    for event in events:
        if any(tag in event.profile.tags for tag in tags) or event.important:
            lst.append({
                'event_id': event.id,
                'profile': request.build_absolute_uri(event.profile.profile_picture.url) if event.profile.profile_picture else None,
                'username': event.profile.username,
                'contact': event.profile.phone_number,
                'category' : event.profile.category,
                'data': request.build_absolute_uri(event.data.url) if event.data else None,
                'description': event.description,
                'url': event.url
            })
    random.shuffle(lst)
    return Response({'events': lst[:25]})

@api_view(['POST'])
def update_profile(request):
    phone_number = request.data.get('phone')    
    user = Profile.objects.get(phone_number = phone_number)

    profile = request.data.get('profile')
    if profile.startswith("/"):
        user.profile_picture = profile
    user.username = request.data.get('username')
    user.email = request.data.get('email')         
    user.category = request.data.get('category')
    user.bio = request.data.get('bio')
    user.description = request.data.get('description')
    user.location = request.data.get('location')
    user.pg_institute = request.data.get('pgInstitute')
    user.pg_year = request.data.get('pgYear')
    user.ug_institute = request.data.get('ugInstitute')
    user.ug_year = request.data.get('ugYear')
    user.school = request.data.get('school')
    user.school_year = request.data.get('schoolYear')
    user.save()
    return Response()
    
@api_view(['POST'])
def get_profile(request):
    phone = request.data.get('phone')
    user = Profile.objects.get(phone_number = phone)
    data ={
        'username': user.username,
        'contact': user.phone_number,
        'email':user.email,
        'profile': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
        'category':user.category,
        'location': user.location,
        'bio': user.bio,
        'description': user.description,
        'pgInstitute': user.pg_institute,
        'pgYear': user.pg_year,
        'ugInstitute': user.ug_institute,
        'ugYear': user.ug_year,
        'school': user.school,
        'schoolYear': user.school_year,
    }
    return Response({'data':data})

@api_view(['POST'])
def createPost(request):
    from .models import Profile, Post
    phone = request.data.get('phone')
    data = request.data.get('data')
    description = request.data.get('description')
    
    user = Profile.objects.get(phone_number = phone)
    post = Post.objects.create(
        profile = user,
        data = data,
        description = description,
        date = datetime.now(),
    )
    return Response()

@api_view(['POST'])
def createEvent(request):
    phone = request.data.get('phone')
    data = request.data.get('data')
    description = request.data.get('description')
    url = request.data.get('url')
    
    user = Profile.objects.get(phone_number = phone)
    event = Event.objects.create(
        profile = user,
        data = data,
        description = description,
        url = url,
        date = datetime.now()
    )
    return Response()
