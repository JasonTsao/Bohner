from django.contrib import admin
from models import *

admin.site.register(Event)
admin.site.register(EventComment)
admin.site.register(EventNotification)
admin.site.register(InvitedFriend)

