from django.conf import settings # type: ignore
from django.urls import path, include # type: ignore
from django.conf.urls.static import static # type: ignore
from . import views

urlpatterns = [
    path("",views.index, name='index'),
    path('contact/', views.handle_contact_form, name='handle_contact_form'),
    path('download/', views.download_apk, name='download'),
    
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)