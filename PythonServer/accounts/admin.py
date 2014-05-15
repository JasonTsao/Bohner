from django.contrib import admin
from models import *

admin.site.register(Account)
admin.site.register(AccountLink)
admin.site.register(AccountSettings)
admin.site.register(AccountSetting)
admin.site.register(AccountDeviceID)
admin.site.register(FacebookProfile)
admin.site.register(VenmoProfile)
admin.site.register(Group)
admin.site.register(UserLocation)

