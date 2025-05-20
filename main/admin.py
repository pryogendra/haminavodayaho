from django.contrib import admin
from .models import *

admin.site.site_title = "HamiNavodyaHo"
admin.site.site_header = "HAMINAVODAYAHO AdminPanel"
admin.site.index_title = "haminavodyaho Dashboard"

# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'phone_number')
    #search_fields = ('username',)
admin.site.register(Profile, ProfileAdmin)

admin.site.register(Post)
admin.site.register(Event)
admin.site.register(Message)
admin.site.register(Inbox)
admin.site.register(CallRecord)

admin.site.register(EventClicked)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Share)

