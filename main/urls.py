from django.conf import settings # type: ignore
from django.urls import path, include # type: ignore
from django.conf.urls.static import static # type: ignore
from . import views

urlpatterns = [
    path("",views.home),
    path('sendMobileOTP/', views.sendMobileOTP),
    path('sendEmailOTP/', views.sendEmailOTP),
    path('registerMobile/', views.registerMobile),
    path('getAllUser/', views.getAllUser),
    path('getAllPost/', views.getAllPost),
    path('getAllEvent/', views.getAllEvent),
    path('updateProfile/', views.update_profile),
    path('getProfile/', views.get_profile),
    
    path('createPost/', views.createPost),
    path('createEvent/', views.createEvent),
        
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)