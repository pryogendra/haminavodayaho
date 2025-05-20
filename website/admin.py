from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Feature)
admin.site.register(Screenshot)
admin.site.register(ContactMessage)
admin.site.register(AboutSection)
admin.site.register(HeroSection)
admin.site.register(myApkFile)