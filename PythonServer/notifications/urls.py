from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required

urlpatterns = patterns("notifications.api",
                        url(r"^create_notification", "createNotification"),
                        url(r"^register_device", "registerDevice"),
                        url(r"^device_details", "getDeviceDetails"),
                        )