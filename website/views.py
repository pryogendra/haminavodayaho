from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from .models import *

# Create your views here.
def index(request):
    context = {
        "features": Feature.objects.all(),
        "screenshots": Screenshot.objects.all(),
        "about": AboutSection.objects.first(),
        "hero": HeroSection.objects.first()
    }
    return render(request, 'website/index.html', context)

def handle_contact_form(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if full_name and email and message:
            ContactMessage.objects.create(
                full_name=full_name,
                email=email,
                message=message
            )
        return redirect('index')
    
def download_apk(request, apk = 1):
    apk = get_object_or_404(myApkFile, id=apk)
    
    file_path = apk.file.path
    
    try:
        response = FileResponse(open(file_path, 'rb'), content_type='application/vnd.android.package-archive')
        response['Content-Disposition'] = f'attachment; filename="{apk.title}.apk"'
        return response
    except FileNotFoundError:
        return HttpResponse("File not found", status=404)
