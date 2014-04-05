from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required

urlpatterns = patterns("notifications.api",
                        url(r"^create_notification", "createNotification"),
                        url(r"^create_apn_service", "createAPNService"),
                        url(r"^register_device", "registerDevice"),
                        url(r"^register_user_to_device/(\d+)", "registerUserToDevice"),
                        url(r"^update_device", "updateDevice"),
                        url(r"^device_details/(\d+)", "getDeviceDetails"),
                        url(r"^test_ios_notifications", "testIOSNotificationAPI"),
                        )